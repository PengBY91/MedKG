# LLM 配置完整指南

## 📋 配置概述

系统已更新为从 `/backend/.env` 文件读取 LLM 配置，移除了所有 Mock 数据。

---

## ✅ 已完成的改进

1. **明确指定 .env 路径** - `backend/app/core/llm.py` 现在明确从 `backend/.env` 加载配置
2. **移除所有 Mock** - 使用真实 LLM API
3. **友好错误提示** - LLM 不可用时显示清晰的配置指引
4. **配置验证脚本** - 提供 `verify_llm_config.py` 检查配置

---

## 🚀 快速配置（3 步）

### 步骤 1：创建 .env 文件

```bash
cd /Users/steve/work/智能体平台/MedKG/backend

# 如果已有 .env 文件，检查内容
cat .env

# 如果没有，创建新文件
touch .env
```

### 步骤 2：编辑 .env 文件

在 `backend/.env` 中添加以下内容：

```bash
# OpenAI 配置（必填）
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
```

**如果使用 DeepSeek**:
```bash
OPENAI_API_KEY=sk-your-deepseek-key
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

### 步骤 3：验证配置

```bash
cd /Users/steve/work/智能体平台/MedKG/backend
python verify_llm_config.py
```

**期望输出**:
```
============================================================
LLM 配置验证
============================================================

1. 检查 .env 文件
   路径: /Users/steve/work/智能体平台/MedKG/backend/.env
   存在: ✓ 是
   ✓ 已加载 .env 文件

2. 检查环境变量
   OPENAI_API_KEY: ✓ 已设置
                   sk-...xxxx
   OPENAI_BASE_URL: ✓ 已设置
                    https://api.openai.com/v1
   OPENAI_MODEL: ✓ 已设置
                 gpt-4

3. 测试 LLM 服务初始化
   ✓ LLM 客户端初始化成功
   模型: gpt-4
   Base URL: https://api.openai.com/v1

4. 建议
   ✓ 配置正确，可以使用问答功能

============================================================
```

---

## 🔧 配置文件路径

### 正确的路径结构

```
MedKG/
├── backend/
│   ├── .env                    ← LLM 配置文件（在这里）
│   ├── .env.example           ← 配置模板
│   ├── verify_llm_config.py   ← 验证脚本
│   └── app/
│       └── core/
│           └── llm.py         ← 读取配置
```

### 配置加载逻辑

```python
# backend/app/core/llm.py

# 1. 确定 .env 文件路径
backend_dir = Path(__file__).parent.parent.parent  # 到达 backend/
env_path = backend_dir / ".env"

# 2. 加载环境变量
if env_path.exists():
    load_dotenv(env_path)  # 从指定路径加载
    print(f"✓ Loaded .env from: {env_path}")
else:
    load_dotenv()  # 回退到默认搜索
```

---

## 📝 完整的 .env 文件示例

```bash
# ============================================
# MedKG LLM 配置
# ============================================

# OpenAI API 配置（必填）
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

# 或使用 DeepSeek
# OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
# OPENAI_BASE_URL=https://api.deepseek.com/v1
# OPENAI_MODEL=deepseek-chat

# ============================================
# 数据库配置（可选）
# ============================================
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=medkg2024

# ============================================
# Redis 缓存（可选）
# ============================================
REDIS_HOST=localhost
REDIS_PORT=6379

# ============================================
# JWT 配置（可选）
# ============================================
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## 🔄 重启服务

配置完成后，重启服务以加载新配置：

```bash
cd /Users/steve/work/智能体平台/MedKG
./start.sh restart
```

查看启动日志确认配置加载：

```bash
./start.sh logs backend | grep -i "llm\|openai"
```

**期望日志**:
```
✓ Loaded .env from: /Users/steve/work/智能体平台/MedKG/backend/.env
[INFO] OpenAI Core Client initialized with base_url=https://api.openai.com/v1, model=gpt-4
```

---

## 🎯 测试问答功能

### 1. 访问问答页面

```
http://localhost:3000/explanation
```

### 2. 提问测试

```
门诊透析费用有限额吗？
```

### 3. 正常响应

```
🤖 AI 助手

根据《基本医疗保险门诊特殊疾病管理规定（2024版）》...
```

### 4. 配置错误响应

```
🤖 AI 助手

⚠️ LLM 服务暂时不可用

请检查系统配置中的 OPENAI_API_KEY 和 OPENAI_BASE_URL 设置。

您可以在"系统配置"页面进行配置。
```

---

## ❌ 故障排除

### 问题 1: 提示 "LLM 服务不可用"

**症状**:
- 页面显示红色错误提示
- 后端日志：`OPENAI_API_KEY not set in Core LLMService`

**解决**:
```bash
# 1. 检查 .env 文件是否存在
ls -la /Users/steve/work/智能体平台/MedKG/backend/.env

# 2. 检查文件内容
cat /Users/steve/work/智能体平台/MedKG/backend/.env | grep OPENAI

# 3. 运行验证脚本
cd /Users/steve/work/智能体平台/MedKG/backend
python verify_llm_config.py

# 4. 确保重启了服务
cd ..
./start.sh restart
```

### 问题 2: API Key 无效

**症状**:
- 后端日志：`LLM generation failed: Error code: 401`

**解决**:
```bash
# 1. 验证 API Key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"

# 2. 检查 Key 是否过期
# 3. 确认 Base URL 正确
# 4. 更新 .env 中的 Key
```

### 问题 3: .env 文件未加载

**症状**:
- 启动日志没有显示 "✓ Loaded .env from..."

**解决**:
```bash
# 确保文件路径正确
pwd  # 应该在 backend 目录
ls -la .env

# 检查文件权限
chmod 644 .env

# 确认文件不为空
wc -l .env
```

### 问题 4: 网络连接问题

**症状**:
- `LLM 调用失败: Connection timeout`

**解决**:
```bash
# 测试网络连接
curl -I https://api.openai.com

# 如果在国内，可能需要配置代理或使用国内镜像
# 例如使用 DeepSeek
OPENAI_BASE_URL=https://api.deepseek.com/v1
```

---

## 📊 支持的 LLM 提供商

| 提供商 | Base URL | 模型示例 |
|--------|----------|----------|
| OpenAI | `https://api.openai.com/v1` | `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo` |
| Azure OpenAI | `https://{resource}.openai.azure.com/` | `gpt-4`, `gpt-35-turbo` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-turbo`, `qwen-max` |
| 月之暗面 | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| 智谱AI | `https://open.bigmodel.cn/api/paas/v4/` | `glm-4` |

---

## 🔒 安全最佳实践

### 1. 保护 API Key

```bash
# ✓ 使用 .env 文件
OPENAI_API_KEY=sk-xxx

# ✗ 不要硬编码
client = OpenAI(api_key="sk-xxx")  # 危险！
```

### 2. .gitignore 配置

确保 `.env` 文件不会被提交：

```bash
# .gitignore
.env
*.env
.env.local
```

### 3. 权限控制

```bash
# 限制文件访问权限
chmod 600 backend/.env
```

### 4. 密钥轮换

- 定期更新 API Key
- 使用不同的 Key 用于开发和生产
- 监控 API 使用量

---

## 📞 需要帮助？

1. **运行验证脚本**: `python backend/verify_llm_config.py`
2. **查看文档**: `docs/REMOVE_MOCK_LLM.md`
3. **查看日志**: `./start.sh logs backend`

---

**文档版本**: v1.0  
**更新日期**: 2024-12-28  
**维护者**: MedKG 开发团队

