# AI 思考过程展示功能

## 功能概述

在流式问答中增加 **AI 思考过程**的展示，让用户了解 AI 的推理思路，增强可解释性和信任度。

## 功能特点

### 1. 两阶段生成
```
第一阶段：思考过程（Thinking Process）
  ↓ 
第二阶段：正式答案（Answer）
```

### 2. 可折叠显示
- 默认折叠，不干扰正常阅读
- 用户可点击展开查看详细思考过程
- 与正式答案视觉区分明显

### 3. 样式区分

#### 思考过程
- 🟡 **黄色调**：温暖的思考氛围
- 📦 **可折叠面板**：节省空间
- 🔖 **特殊标识**："AI 思考过程" + 橙色图标
- 📝 **左边框强调**：金黄色左边框

#### 正式答案
- ⚪ **灰白色**：正式、权威
- 📄 **直接显示**：主要内容
- ✨ **清晰易读**：标准字体和间距

## 实现效果

### 视觉示例

```
┌─────────────────────────────────────┐
│ 用户问题：糖尿病门诊费用限额？      │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ 🤖 AI 回复                          │
│                                     │
│ 根据医保政策...（正式答案内容）    │
│                                     │
│ ┌─ 💭 AI 思考过程 [点击展开] ─────┐│
│ │ [折叠状态]                       ││
│ └─────────────────────────────────┘│
│                                     │
│ 📊 图谱协同推理链路 [点击展开]     │
│                                     │
│ 📚 依据条文：政策A、政策B...        │
└─────────────────────────────────────┘
```

### 展开后

```
┌─ 💭 AI 思考过程 [点击收起] ─────────┐
│                                     │
│  问题理解：                         │
│  用户询问糖尿病门诊费用限额政策    │
│                                     │
│  信息分析：                         │
│  检索到3条相关政策规则，包含...    │
│                                     │
│  推理逻辑：                         │
│  首先确认糖尿病属于慢性病管理...    │
│                                     │
│  关键要点：                         │
│  重点说明限额标准和报销比例        │
└─────────────────────────────────────┘
```

## 技术实现

### 后端实现

#### 1. 思考过程生成

```python
# backend/app/api/api_v1/endpoints/explanation.py

# 构建思考过程的 prompt
thinking_prompt = f"""
请分析以下问题，并展示你的思考过程：

问题：{question}

已检索到的相关政策规则：
{sources}

识别的实体：
{entities}

请按照以下步骤思考（简洁）：
1. 问题理解：这个问题的核心是什么？
2. 信息分析：检索到的政策规则是否相关？
3. 推理逻辑：如何组织答案？
4. 关键要点：需要特别强调的内容？

请用 200 字以内简明扼要地展示思考过程。
"""

# 流式生成思考过程
yield {"type": "thinking_start"}
async for chunk in llm_provider.generate_stream(thinking_prompt):
    yield {"type": "thinking", "content": chunk}
yield {"type": "thinking_done"}

# 然后生成正式答案
yield {"type": "answer_start"}
async for chunk in llm_provider.generate_stream(answer_prompt):
    yield {"type": "chunk", "content": chunk}
```

#### 2. SSE 事件类型

| 事件类型 | 说明 | 数据格式 |
|---------|------|---------|
| `thinking_start` | 思考开始 | `{"type": "thinking_start"}` |
| `thinking` | 思考片段 | `{"type": "thinking", "content": "..."}` |
| `thinking_done` | 思考完成 | `{"type": "thinking_done"}` |
| `answer_start` | 答案开始 | `{"type": "answer_start"}` |
| `chunk` | 答案片段 | `{"type": "chunk", "content": "..."}` |
| `done` | 全部完成 | `{"type": "done", "full_answer": "...", "full_thinking": "..."}` |

### 前端实现

#### 1. API 调用

```javascript
// frontend/src/services/api.js

await api.queryPolicyStream(question, sessionId, {
    // 思考过程回调
    onThinking: (chunk) => {
        message.thinking += chunk
    },
    onThinkingDone: () => {
        console.log('Thinking completed')
    },
    // 答案回调
    onAnswerStart: () => {
        message.loading = false
    },
    onChunk: (chunk) => {
        message.content += chunk
    },
    // 元数据回调
    onMetadata: (data) => {
        message.sources = data.sources
        message.reasoning_trace = data.reasoning_trace
    }
})
```

#### 2. Vue 组件

```vue
<!-- 思考过程显示 -->
<div v-if="msg.thinking && msg.thinking.trim()" class="thinking-section">
  <el-collapse class="thinking-collapse">
    <el-collapse-item name="thinking">
      <template #title>
        <div class="thinking-header">
          <el-icon class="thinking-icon"><DataAnalysis /></el-icon>
          <span class="thinking-label">AI 思考过程</span>
          <el-tag size="small" type="warning" effect="plain">点击展开</el-tag>
        </div>
      </template>
      <div class="thinking-content">
        {{ msg.thinking }}
      </div>
    </el-collapse-item>
  </el-collapse>
</div>
```

#### 3. 样式设计

```css
/* 思考过程容器 - 黄色主题 */
.thinking-collapse {
  border: 2px solid #ffeaa7;
  border-radius: 12px;
  background: #fffbf0;
}

/* 思考过程头部 */
.thinking-collapse :deep(.el-collapse-item__header) {
  background: #fff9e6;
  padding: 12px 16px;
}

.thinking-collapse :deep(.el-collapse-item__header:hover) {
  background: #fff4d1;
}

/* 思考内容 */
.thinking-content {
  color: #5f3e31;
  line-height: 1.8;
  padding: 12px;
  background: white;
  border-radius: 8px;
  border-left: 4px solid #fdcb6e;
  white-space: pre-wrap;
}
```

## 用户体验

### 优势

1. **透明性** ✨
   - 用户能看到 AI 的推理过程
   - 增强对答案的信任度

2. **可选性** 🎯
   - 默认折叠，不干扰阅读
   - 需要时可以展开查看

3. **教育性** 📚
   - 帮助用户理解 AI 如何思考
   - 学习如何更好地提问

4. **调试性** 🔧
   - 开发者可以查看推理链路
   - 便于优化 prompt 和模型

### 交互流程

```
用户提问
  ↓
显示加载动画（800ms）
  ↓
思考过程流式显示（2-3秒）
  - 逐字显示思考内容
  - 自动折叠
  ↓
正式答案流式显示（2-3秒）
  - 逐字显示答案内容
  ↓
显示推理链路（折叠）
  ↓
显示来源文档
```

## 性能优化

### 1. 并行生成
- 思考过程和答案分开生成
- 思考完成后立即开始答案生成
- 总耗时：思考时间 + 答案时间

### 2. 长度控制
```python
# 限制思考过程长度
"请用 200 字以内简明扼要地展示思考过程。"
```

### 3. 可选开关
```python
# 可配置是否生成思考过程
enable_thinking = os.getenv("ENABLE_THINKING_PROCESS", "true")
```

## 配置选项

### 环境变量

```bash
# .env
ENABLE_THINKING_PROCESS=true  # 是否启用思考过程
THINKING_MAX_LENGTH=200       # 思考过程最大字数
THINKING_TEMPERATURE=0.7      # 思考过程温度（创造性）
```

### 前端配置

```javascript
// 可配置默认展开/折叠
const thinkingDefaultExpanded = false

// 可配置是否显示
const showThinkingProcess = true
```

## 示例效果

### 问题：糖尿病门诊费用限额是多少？

#### 思考过程（折叠）
```
问题理解：
用户询问糖尿病患者门诊费用的报销限额政策

信息分析：
检索到3条相关政策，涉及慢性病管理和门诊特殊疾病

推理逻辑：
1. 确认糖尿病属于慢性病范畴
2. 查找门诊特殊疾病政策
3. 提取具体限额标准

关键要点：
需要说明限额标准、报销比例和申请流程
```

#### 正式答案
```
根据医保政策，糖尿病作为慢性病纳入门诊特殊疾病管理：

1. 费用限额：
   - 每月最高限额：420元
   - 年度累计限额：5040元

2. 报销比例：
   - 一级医院：85%
   - 二级医院：75%
   - 三级医院：65%

3. 申请条件：
   - 需提供相关诊断证明
   - 经医保部门审核通过

详情请参考以下政策文件...
```

## 文件变更

- ✅ `backend/app/api/api_v1/endpoints/explanation.py` - 添加思考过程生成逻辑
- ✅ `frontend/src/services/api.js` - 添加思考过程回调
- ✅ `frontend/src/views/ExplanationQuery.vue` - 添加思考过程UI和样式

## 未来优化

1. **思考深度控制**：允许用户选择简单/详细模式
2. **思考过程缓存**：避免重复问题重复思考
3. **思考过程评分**：让用户反馈思考质量
4. **多语言支持**：思考过程支持多语言展示
5. **可视化思考**：用思维导图展示推理链路

