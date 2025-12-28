# 移除 Mock LLM，使用真实 LLM 服务

## 🎯 更新内容

已将所有 Mock LLM 替换为真实的 LLM 服务。如果 LLM 不可用，系统会显示友好的错误提示。

---

## ✅ 主要变更

### 1. 后端 API 更新

**文件**: `backend/app/api/api_v1/endpoints/explanation.py`

**变更内容**:
- ❌ 移除 `MockLLMProvider`
- ✅ 使用 `RealLLMProvider` 直接调用 OpenAI API
- ✅ 添加 LLM 可用性检查
- ✅ 返回 503 错误当 LLM 不可用

**新增的 LLM Provider**:
```python
class RealLLMProvider:
    """真实的 LLM Provider，不使用 Mock"""
    
    async def generate(self, prompt: str, schema: Dict = None) -> str:
        client = llm_service.get_client()
        if not client:
            raise HTTPException(
                status_code=503,
                detail="LLM 服务不可用，请检查 OPENAI_API_KEY 配置"
            )
        
        try:
            response = await client.chat.completions.create(
                model=llm_service.get_model_name(),
                messages=[
                    {"role": "system", "content": "你是一位专业的医保政策助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"LLM 调用失败: {str(e)}"
            )
```

---

### 2. 前端错误处理

**文件**: `frontend/src/views/ExplanationQueryEnhanced.vue`

**变更内容**:
- ✅ 识别 503 错误（LLM 不可用）
- ✅ 显示友好的错误提示
- ✅ 指引用户到系统配置页面
- ✅ 添加错误消息特殊样式

**错误处理逻辑**:
```javascript
if (status === 503) {
  // LLM 服务不可用
  errorMessage = `⚠️ LLM 服务暂时不可用

请检查系统配置中的 OPENAI_API_KEY 和 OPENAI_BASE_URL 设置。

您可以在"系统配置"页面进行配置。`
  
  ElMessage.error({
    message: 'LLM 服务不可用，请联系管理员配置',
    duration: 5000,
    showClose: true
  })
}
```

**错误消息样式**:
- 红色背景 (#fef0f0)
- 红色左边框 (3px solid #f56c6c)
- 红色文字 (#f56c6c)

---

## 📋 配置 LLM 服务

### 方式1: 环境变量（推荐）

创建 `.env` 文件：

```bash
# OpenAI 配置
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

# 或使用兼容的API（如 DeepSeek）
OPENAI_API_KEY=sk-your-deepseek-key
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

### 方式2: 系统配置页面

1. 访问：`http://localhost:3000/system`
2. 点击"LLM 配置"选项卡
3. 填写以下信息：
   - API Key
   - Base URL
   - Model Name
4. 点击"保存配置"

### 方式3: 直接修改代码

编辑 `backend/app/core/llm.py`：

```python
def _init_client(self):
    self.client = AsyncOpenAI(
        api_key="your-api-key",
        base_url="https://api.openai.com/v1"
    )
    self.model = "gpt-4"
```

---

## 🚀 使用流程

### 1. 配置 LLM（首次使用）

```bash
# 设置环境变量
export OPENAI_API_KEY="sk-your-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_MODEL="gpt-4"

# 重启后端服务
cd /Users/steve/work/智能体平台/MedKG
./start.sh restart
```

### 2. 测试 LLM 连接

```bash
# 查看后端日志
./start.sh logs backend

# 应该看到：
# [INFO] OpenAI Core Client initialized with base_url=..., model=gpt-4
```

### 3. 使用问答功能

访问：`http://localhost:3000/explanation`

**正常情况**:
- 输入问题
- AI 返回答案
- 显示推理链路和来源

**LLM 不可用时**:
- 显示红色错误提示
- 提示检查配置
- 指引到系统配置页面

---

## 🎨 错误提示示例

### 前端显示

```
🤖 AI 助手

┌───────────────────────────────────┐
│ ⚠️ LLM 服务暂时不可用              │
│                                    │
│ 请检查系统配置中的 OPENAI_API_KEY  │
│ 和 OPENAI_BASE_URL 设置。          │
│                                    │
│ 您可以在"系统配置"页面进行配置。   │
└───────────────────────────────────┘
```

### 后端日志

```
[ERROR] LLM generation failed: Error code: 401 - {'error': ...}
[WARNING] OPENAI_API_KEY not set in Core LLMService.
```

---

## 🔧 故障排除

### 问题 1: 提示 "LLM 服务不可用"

**原因**: 
- OPENAI_API_KEY 未设置
- API Key 无效
- 网络连接问题

**解决方案**:
```bash
# 1. 检查环境变量
echo $OPENAI_API_KEY

# 2. 查看配置
curl http://localhost:8000/api/v1/system/llm/config \
  -H "Authorization: Bearer YOUR_TOKEN"

# 3. 重新配置
export OPENAI_API_KEY="sk-valid-key"
./start.sh restart
```

### 问题 2: API 调用失败

**原因**:
- API Key 额度不足
- Rate limit 限制
- Base URL 错误

**解决方案**:
```bash
# 测试 API 连接
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# 检查日志
tail -f /tmp/medkg_backend.log | grep LLM
```

### 问题 3: 响应超时

**原因**:
- 模型生成时间过长
- 网络延迟

**解决方案**:
修改超时设置：

```python
# backend/app/api/api_v1/endpoints/explanation.py
response = await client.chat.completions.create(
    ...,
    timeout=30.0  # 增加超时时间
)
```

---

## 📊 API 响应格式

### 成功响应

```json
{
  "question": "门诊透析费用有限额吗？",
  "answer": "根据政策...",
  "sources": [...],
  "reasoning_trace": [...],
  "session_id": "conv_abc123",
  "metadata": {
    "pipeline_version": "enhanced-v2-multiturn",
    "has_conversation_context": true
  }
}
```

### 错误响应（LLM 不可用）

```json
{
  "detail": "LLM 服务不可用，请检查 OPENAI_API_KEY 配置"
}
```

HTTP 状态码: `503 Service Unavailable`

### 错误响应（LLM 调用失败）

```json
{
  "detail": "LLM 调用失败: Error code: 429 - Rate limit exceeded"
}
```

HTTP 状态码: `503 Service Unavailable`

---

## 🔄 与原 Mock 的对比

| 特性 | Mock LLM | Real LLM |
|------|----------|----------|
| **响应来源** | 硬编码文本 | OpenAI API |
| **回答质量** | 固定模板 | 真实 AI 生成 |
| **上下文理解** | ❌ 不支持 | ✅ 完整支持 |
| **多轮对话** | ❌ 简单模拟 | ✅ 真实理解 |
| **错误处理** | 返回 JSON 错误 | 友好提示 |
| **配置需求** | 无需配置 | 需要 API Key |
| **成本** | 免费 | 按 token 计费 |

---

## ⚠️ 重要提示

### 1. API Key 安全
- ❌ 不要将 API Key 提交到 Git
- ✅ 使用 .env 文件（已在 .gitignore 中）
- ✅ 使用环境变量管理
- ✅ 定期轮换 API Key

### 2. 成本控制
- 设置 max_tokens 限制（当前 2000）
- 监控 API 使用量
- 考虑使用缓存减少重复调用

### 3. 备用方案
- 配置多个 API 提供商
- 实现降级逻辑
- 准备离线模式

---

## 📝 下一步改进

1. **多 LLM 支持**
   - 支持切换不同的 LLM 提供商
   - Azure OpenAI, Anthropic Claude 等

2. **智能重试**
   - API 失败时自动重试
   - 指数退避策略

3. **缓存机制**
   - 缓存常见问题的答案
   - 减少 API 调用成本

4. **流式输出**
   - 支持 Server-Sent Events
   - 实时显示生成内容

5. **成本监控**
   - 记录每次调用的 token 数
   - 生成使用报告

---

## ✅ 验证清单

- [x] 移除所有 MockLLMProvider 引用
- [x] 实现 RealLLMProvider
- [x] 添加 LLM 可用性检查
- [x] 前端错误处理
- [x] 友好的错误提示
- [x] 错误消息样式
- [x] 指引用户配置
- [x] 后端异常处理
- [x] 日志记录
- [x] 文档更新

---

**文档版本**: v1.0  
**更新日期**: 2024-12-28  
**维护者**: MedKG 开发团队  
**状态**: ✅ 已完成

