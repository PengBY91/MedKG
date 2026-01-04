# MedKG - 医学知识图谱系统

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![KAG](https://img.shields.io/badge/KAG-0.8.0-green.svg)](https://github.com/OpenSPG/KAG)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

MedKG 是一个集成了 **KAG (Knowledge Augmented Generation)** 框架的医学知识图谱系统,提供智能文档处理、知识抽取、图谱构建和智能问答能力。

## ✨ 核心特性

- 🚀 **智能知识构建** - 自动从医学文档提取实体和关系,构建知识图谱
- 🧠 **多跳推理问答** - 基于图谱的多跳推理,提供可解释的答案
- 🔍 **混合检索** - 结合向量检索和图谱检索,提高准确率
- 📊 **可视化界面** - 直观的知识图谱可视化和交互式问答
- 🔌 **REST API** - 完整的 API 接口,易于集成
- 🐳 **容器化部署** - Docker Compose 一键部署

## 📁 项目结构

```
MedKG/
├── backend/                 # 后端服务 (FastAPI + Python)
│   └── app/
│       ├── api/            # REST API 端点
│       ├── services/       # 核心业务服务
│       │   ├── kag_medical_builder.py    # 知识构建服务
│       │   ├── kag_solver_service.py     # 问答服务
│       │   ├── schema_service.py         # Schema 管理
│       │   └── ...
│       ├── core/           # 核心配置
│       └── models/         # 数据模型
├── frontend/               # 前端应用 (Vue 3)
│   ├── src/
│   │   ├── components/    # UI 组件
│   │   ├── views/         # 页面视图
│   │   └── api/           # API 调用
│   └── public/
├── config/                 # 配置文件
│   └── kag_config.yaml    # KAG 主配置
├── docker/                 # Docker 配置
│   ├── docker-compose-neo4j.yml
│   └── openspg-docker-compose.yml
├── docs/                   # 项目文档
│   ├── kag/               # KAG 集成文档
│   │   ├── README.md              # KAG 快速开始
│   │   ├── developer_manual.md    # 开发者手册
│   │   └── integration_guide.md   # 集成指南
│   ├── deployment/        # 部署文档
│   └── reports/           # 项目报告
├── scripts/               # 工具脚本
│   ├── init/             # 初始化脚本
│   │   ├── init_project.py       # 初始化 OpenSPG 项目
│   │   └── init_schema.py        # 初始化知识图谱 Schema
│   ├── test/             # 测试脚本
│   │   ├── test_builder.py       # 测试知识构建
│   │   ├── test_solver.py        # 测试问答服务
│   │   └── test_e2e.py          # 端到端测试
│   └── verify/           # 验证脚本
│       ├── verify_config.py      # 验证配置
│       └── verify_services.py    # 验证服务
├── docker-compose.yml     # 主 Docker Compose 配置
├── start.sh              # 服务启动脚本
└── README.md             # 本文件
```

## 🚀 快速开始

### 前置要求

- **Python**: 3.10+
- **Node.js**: 16+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Conda**: (推荐)

### 1. 克隆项目

```bash
git clone <repository-url>
cd MedKG
```

### 2. 环境配置

```bash
# 创建并激活 conda 环境
conda create -n medical python=3.10
conda activate medical

# 安装 Python 依赖
pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install
cd ..
```

### 3. 启动基础服务

```bash
# 启动 OpenSPG、Neo4j、PostgreSQL 等服务
docker compose up -d

# 等待服务启动完成 (约 30 秒)
docker ps
```

### 4. 初始化系统

```bash
# 初始化 OpenSPG 项目
python scripts/init/init_project.py

# 初始化知识图谱 Schema
python scripts/init/init_schema.py
```

### 5. 启动应用

```bash
# 启动后端和前端服务
./start.sh start

# 或分别启动
./start.sh start backend
./start.sh start frontend
```

### 6. 访问系统

- **前端界面**: http://localhost:3000
- **后端 API**: http://127.0.0.1:8001
- **API 文档**: http://127.0.0.1:8001/docs
- **OpenSPG**: http://127.0.0.1:8887
- **Neo4j**: http://localhost:7474

## 💡 使用示例

### 1. 上传医学文档

```bash
curl -X POST http://127.0.0.1:8001/api/kag/build/document \
  -F "file=@medical_document.pdf"
```

### 2. 智能问答

```bash
curl -X POST http://127.0.0.1:8001/api/kag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "糖尿病的主要症状有哪些?",
    "context": {}
  }'
```

### 3. Python SDK

```python
from backend.app.services.kag_medical_builder import kag_builder
from backend.app.services.kag_solver_service import kag_solver

# 构建知识图谱
result = kag_builder.build_document('/path/to/document.pdf')

# 智能问答
import asyncio
answer = asyncio.run(kag_solver.solve_query("糖尿病的治疗方法?"))
print(answer['answer'])
```

## 🧪 测试

```bash
# 测试知识构建
python scripts/test/test_builder.py

# 测试问答服务
python scripts/test/test_solver.py

# 端到端测试
python scripts/test/test_e2e.py

# 验证所有服务
python scripts/verify/verify_services.py
```

## ⚙️ 配置说明

主配置文件: `config/kag_config.yaml`

```yaml
# 项目配置
project:
  id: "1"
  namespace: "MedicalGovernance"
  host_addr: "http://127.0.0.1:8887"

# LLM 配置
chat_llm:
  type: openai
  base_url: "https://api.huiyan-ai.cn/v1"
  api_key: "${OPENAI_API_KEY}"
  model: "deepseek-chat"

# 向量化模型配置
vectorize_model:
  type: openai
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  api_key: "${OPENAI_API_KEY}"
  model: "text-embedding-v4"
  vector_dimensions: 1536

# 知识构建配置
unstructured_builder:
  chain:
    reader:
      type: txt_reader
    splitter:
      type: length_splitter
      split_length: 800
      window_length: 100
    extractor:
      type: schema_free_extractor
    vectorizer:
      type: batch_vectorizer
    writer:
      type: kg_writer
```

### 环境变量

创建 `.env` 文件:

```bash
# LLM API Key
OPENAI_API_KEY=your-api-key

# 项目配置
KAG_PROJECT_ID=1
KAG_HOST=http://127.0.0.1:8887

# 数据库配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

## 📚 技术栈

### 后端

- **KAG Framework**: 0.8.0 - 知识增强生成框架
- **OpenSPG**: Latest - 知识图谱平台
- **FastAPI**: 现代 Python Web 框架
- **Neo4j**: 5.25.1 (DozerDB) - 图数据库
- **PostgreSQL**: 关系数据库
- **Milvus**: 向量数据库

### 前端

- **Vue 3**: 渐进式 JavaScript 框架
- **Element Plus**: UI 组件库
- **ECharts**: 数据可视化
- **Axios**: HTTP 客户端

### AI 模型

- **LLM**: DeepSeek Chat
- **Embedding**: Text-Embedding-V4

## 🔧 开发指南

### 添加新的实体类型

1. 修改 `scripts/init/init_schema.py`:

```python
entities = [
    {
        "name": "MedicalGovernance.NewEntity",
        "name_zh": "新实体",
        "description": "新实体描述",
        "properties": {
            "propertyName": "Text"
        }
    }
]
```

2. 重新初始化 Schema:

```bash
python scripts/init/init_schema.py
```

### 添加新的 API 端点

在 `backend/app/api/` 下创建新的路由文件,然后在 `backend/app/api/api_v1/api.py` 中注册。

### 自定义知识抽取

修改 `config/kag_config.yaml` 中的 `unstructured_builder` 配置,调整抽取器参数。

## 📖 文档

- **[KAG 开发手册](docs/kag/developer_manual.md)** - 详细的开发指南
- **[集成指南](docs/kag/integration_guide.md)** - KAG 集成步骤
- **[部署指南](docs/deployment/)** - 生产环境部署
- **[API 文档](http://127.0.0.1:8001/docs)** - 交互式 API 文档

## 🐛 故障排查

### 服务启动失败

```bash
# 查看服务日志
docker compose logs -f

# 查看后端日志
tail -f /tmp/medkg_backend.log

# 查看前端日志
tail -f /tmp/medkg_frontend.log
```

### 数据库连接问题

```bash
# 检查 PostgreSQL
docker exec medical_postgres psql -U medical_user -d medical_governance -c "\dt"

# 检查 Neo4j
docker exec medical_neo4j cypher-shell -u neo4j -p password "MATCH (n) RETURN count(n)"
```

### 配置验证

```bash
# 验证 KAG 配置
python scripts/verify/verify_config.py

# 验证所有服务
python scripts/verify/verify_services.py
```

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议!

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 更新日志

### v1.0.0 (2026-01-04)

- ✅ 完成 KAG 框架集成
- ✅ 实现知识构建和问答功能
- ✅ 移除所有 Mock 实现
- ✅ 完善项目文档和测试
- ✅ 优化目录结构

## 📄 License

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 👥 团队

- **开发**: [Your Name]
- **架构**: [Your Name]
- **文档**: [Your Name]

## 🙏 致谢

- [OpenSPG](https://github.com/OpenSPG/openspg) - 知识图谱平台
- [KAG](https://github.com/OpenSPG/KAG) - 知识增强生成框架
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [Vue.js](https://vuejs.org/) - 前端框架

## 📞 联系方式

- **Email**: your-email@example.com
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)

---

**⭐ 如果这个项目对你有帮助,请给我们一个 Star!**
