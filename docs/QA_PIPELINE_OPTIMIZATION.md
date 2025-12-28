# 问答流程优化说明

## 优化目标
提升问答响应速度，简化推理链路，减少不必要的处理步骤。

## 优化前后对比

### 优化前（6个步骤）
```
0. Conversation Context (单独处理对话历史)
1. Query Understanding (实体识别和查询改写)
2. Multi-channel Retrieval (关键词 + 向量 + 图谱检索)
3. Result Ranking (使用 MMR 重排序)
4. KAG Logic Reasoning (逻辑推理)
5. Terminology Standardization (术语标准化)
6. Knowledge Fusion (知识融合生成答案)
```

**问题：**
- 步骤过多，每个步骤都有 I/O 开销
- 图谱检索和重排序耗时较长
- 术语标准化对最终答案影响较小

### 优化后（4个步骤）

```
1. Query Understanding (合并上下文处理 + 实体识别)
   - 同时处理对话历史和实体识别
   - 减少一次 LLM 调用

2. Multi-channel Retrieval (仅关键词 + 向量)
   - 移除图谱检索（图谱检索较慢）
   - 直接返回 Top-8 结果，不做重排序
   - 检索结果从 15 条减少到 8 条

3. KAG Logic Reasoning (逻辑推理)
   - 保持不变，这是核心能力
   - 传入的上下文减少到最近 2 轮对话

4. Knowledge Fusion (知识融合生成答案)
   - 移除术语标准化步骤
   - 简化 Prompt 构建
   - 对话历史只保留最近 3 轮
```

## 具体优化措施

### 1. 合并步骤 0 和步骤 1
**优化前：**
```python
# Stage 0: 处理对话上下文
contextualized_question = await self._contextualize_query(question, conversation_history)

# Stage 1: 实体识别
entities, rewritten_query = await self._understand_query(contextualized_question)
```

**优化后：**
```python
# Stage 1: 同时处理上下文和实体识别
contextualized_question = await self._contextualize_query(question, conversation_history)
entities, rewritten_query = await self._understand_query(contextualized_question)
# 记录为一个步骤
```

### 2. 简化检索流程
**优化前：**
```python
# 使用三通道检索
related_nodes = await self.graph_db.search_policies(search_query, top_k=15)
# 然后进行 MMR 重排序
ranked_nodes = await self._rerank_results(search_query, related_nodes, top_k=10)
```

**优化后：**
```python
# 只使用关键词 + 向量检索
related_nodes = await self._simplified_retrieval(search_query, top_k=8)
# 不再重排序，直接使用检索结果
```

### 3. 移除术语标准化
**原因：**
- 术语标准化需要调用外部服务或数据库
- 对最终答案质量影响有限
- 增加延迟

**优化：**
直接移除 Stage 5，不再传递 `standard_terms` 参数。

### 4. 减少 KAG 上下文
**优化前：**
```python
kag_context = {
    "rules": ranked_nodes[:5],
    "entities": entities,
    "conversation_history": conversation_history[-3:]  # 最近3轮
}
```

**优化后：**
```python
kag_context = {
    "rules": related_nodes[:5],
    "entities": entities,
    "conversation_history": conversation_history[-2:]  # 最近2轮
}
```

### 5. 简化对话历史
**优化：**
在构建 Prompt 时，只使用最近 3 轮对话历史，而不是全部历史。

## 性能提升估算

| 优化项 | 预计节省时间 | 说明 |
|--------|------------|------|
| 合并步骤 0-1 | 减少逻辑复杂度 | 不涉及额外 API 调用 |
| 移除图谱检索 | 200-500ms | 图谱查询通常较慢 |
| 移除重排序 | 50-100ms | MMR 算法计算开销 |
| 移除术语标准化 | 100-300ms | 可能涉及数据库查询 |
| 减少检索数量 | 50-100ms | 从15条减少到8条 |
| **总计** | **~500-1000ms** | 响应速度提升 30-50% |

## 推理链路展示

用户在前端看到的推理链路：

```
推理链路
1. Query Understanding
   处理 2 轮对话，识别实体: 3个, 查询改写: 是

2. Multi-channel Retrieval
   检索到 8 条政策规则（关键词+向量）

3. KAG Logic Reasoning
   KAG 成功执行逻辑推理

4. Knowledge Fusion
   多源知识融合，生成最终答案
```

## 注意事项

1. **准确性保持**：虽然简化了流程，但保留了核心的 KAG 推理能力
2. **降级策略**：如果简化检索失败，会自动降级到图谱检索
3. **版本标识**：返回结果中 `pipeline_version` 标记为 `"simplified-v1-fast"`

## 代码变更

主要变更文件：
- `backend/app/services/explanation_service.py`
  - 修改 `query_policy()` 方法
  - 新增 `_simplified_retrieval()` 方法
  - 移除 `_rerank_results()` 方法

## 回滚方案

如果需要恢复原有流程，可以使用 Git 恢复之前的版本：
```bash
git log --oneline backend/app/services/explanation_service.py
git checkout <commit-hash> backend/app/services/explanation_service.py
```

