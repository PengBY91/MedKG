# OpenAI API 配置说明

## 配置文件位置
`backend/.env`

## 配置项说明

### 必需配置
```bash
# OpenAI API密钥
OPENAI_API_KEY=your_api_key_here

# API基础URL（支持自定义端点）
OPENAI_BASE_URL=https://api.openai.com/v1

# 使用的模型名称
OPENAI_MODEL=gpt-4
```

### 支持的API端点

1. **OpenAI官方**
   ```bash
   OPENAI_BASE_URL=https://api.openai.com/v1
   OPENAI_MODEL=gpt-4
   ```

2. **Azure OpenAI**
   ```bash
   OPENAI_BASE_URL=https://your-resource.openai.azure.com/openai/deployments/your-deployment
   OPENAI_MODEL=gpt-4
   ```

3. **其他兼容端点** (如DeepSeek、智谱AI等)
   ```bash
   OPENAI_BASE_URL=https://api.huiyan-ai.cn/v1
   OPENAI_MODEL=deepseek-chat
   ```


✅ **配置已完成！**

## 代码修改

已修改 `examination_standardization_service.py`:

1. **支持自定义base_url**
   ```python
   base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
   self.llm_client = AsyncOpenAI(
       api_key=api_key,
       base_url=base_url
   )
   ```

2. **支持自定义模型**
   ```python
   self.model = os.getenv("OPENAI_MODEL", "gpt-4")
   
   # 使用时
   response = await self.llm_client.chat.completions.create(
       model=self.model,  # 使用配置的模型
       messages=[{"role": "user", "content": prompt}],
       temperature=0.1,
       max_tokens=500
   )
   ```

## 使用说明

1. **重启后端服务**以应用新配置
   ```bash
   # 停止当前服务 (Ctrl+C)
   # 重新启动
   cd backend
   conda activate medical
   uvicorn app.main:app --reload
   ```

2. **验证配置**
   - 启动日志会显示: `OpenAI client initialized with base_url=... model=...`
   - 上传检查项目文件进行标准化测试

3. **测试LLM功能**
   - 上传 `test_examination_data.csv`
   - 系统将使用配置的LLM进行智能标准化
   - 查看结果验证LLM是否正常工作

## 注意事项

⚠️ **安全提醒**:
- `.env` 文件已在 `.gitignore` 中，不会被提交到Git
- 请勿将API密钥分享给他人
- 定期更换API密钥以确保安全

🔧 **故障排查**:
- 如果LLM调用失败，检查API密钥是否有效
- 确认base_url是否正确
- 查看后端日志获取详细错误信息
