# OpenAI LLM 配置模板

将此文件复制为 `.env` 并填入真实配置。

## 基本配置

```bash
# OpenAI API Key（必填）
OPENAI_API_KEY=sk-your-api-key-here

# OpenAI API Base URL（可选）
OPENAI_BASE_URL=https://api.openai.com/v1

# 使用的模型名称（可选）
OPENAI_MODEL=gpt-4
```

## 支持的 API 提供商

### 1. OpenAI 官方

```bash
OPENAI_API_KEY=sk-your-openai-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
```

### 2. Azure OpenAI

```bash
OPENAI_API_KEY=your-azure-key
OPENAI_BASE_URL=https://your-resource.openai.azure.com/
OPENAI_MODEL=gpt-4
```

### 3. DeepSeek

```bash
OPENAI_API_KEY=sk-your-deepseek-key
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

### 4. 阿里通义千问

```bash
OPENAI_API_KEY=your-dashscope-key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL=qwen-turbo
```

## 验证配置

运行验证脚本检查配置：

```bash
cd backend
python verify_llm_config.py
```

## 配置文件位置

.env 文件应该放在：
```
/Users/steve/work/智能体平台/MedKG/backend/.env
```

## 安全提示

- ⚠️ 不要将 .env 文件提交到 Git
- ⚠️ 不要在代码中硬编码 API Key
- ⚠️ 定期轮换 API Key
- ✓ 使用环境变量管理敏感信息

