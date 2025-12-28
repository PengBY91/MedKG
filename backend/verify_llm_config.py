"""
验证 LLM 配置是否正确加载

运行此脚本检查：
1. .env 文件是否存在
2. 环境变量是否正确加载
3. LLM 客户端是否初始化成功
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv

# Load .env
env_path = backend_dir / ".env"
print(f"\n{'='*60}")
print("LLM 配置验证")
print('='*60)

print(f"\n1. 检查 .env 文件")
print(f"   路径: {env_path}")
print(f"   存在: {'✓ 是' if env_path.exists() else '✗ 否'}")

if env_path.exists():
    load_dotenv(env_path)
    print(f"   ✓ 已加载 .env 文件")
else:
    print(f"   ⚠ .env 文件不存在，尝试从环境变量读取")

print(f"\n2. 检查环境变量")
api_key = os.getenv("OPENAI_API_KEY", "")
base_url = os.getenv("OPENAI_BASE_URL", "")
model = os.getenv("OPENAI_MODEL", "")

print(f"   OPENAI_API_KEY: {'✓ 已设置' if api_key else '✗ 未设置'}")
if api_key:
    masked_key = f"{api_key[:3]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
    print(f"                   {masked_key}")

print(f"   OPENAI_BASE_URL: {'✓ 已设置' if base_url else '✗ 未设置'}")
if base_url:
    print(f"                    {base_url}")

print(f"   OPENAI_MODEL: {'✓ 已设置' if model else '✗ 未设置'}")
if model:
    print(f"                 {model}")

print(f"\n3. 测试 LLM 服务初始化")
try:
    from app.core.llm import llm_service
    
    client = llm_service.get_client()
    if client:
        print(f"   ✓ LLM 客户端初始化成功")
        print(f"   模型: {llm_service.get_model_name()}")
        print(f"   Base URL: {llm_service.get_config()['base_url']}")
    else:
        print(f"   ✗ LLM 客户端初始化失败")
        print(f"   原因: OPENAI_API_KEY 未设置或无效")
        
except Exception as e:
    print(f"   ✗ 初始化出错: {e}")

print(f"\n4. 建议")
if not api_key:
    print(f"   ⚠ 请在 {env_path} 文件中设置 OPENAI_API_KEY")
    print(f"   示例内容：")
    print(f"   ")
    print(f"   OPENAI_API_KEY=sk-your-api-key-here")
    print(f"   OPENAI_BASE_URL=https://api.openai.com/v1")
    print(f"   OPENAI_MODEL=gpt-4")
elif not llm_service.get_client():
    print(f"   ⚠ API Key 可能无效，请检查")
else:
    print(f"   ✓ 配置正确，可以使用问答功能")

print(f"\n{'='*60}\n")

