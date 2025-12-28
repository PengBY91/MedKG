# MedKG: 医疗治理与全域知识资产平台 (v2.4)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Vite](https://img.shields.io/badge/frontend-Vue3-green.svg)
![FastAPI](https://img.shields.io/badge/backend-FastAPI-blue.svg)
![Neo4j](https://img.shields.io/badge/database-Neo4j-red.svg)
![DeepSeek](https://img.shields.io/badge/LLM-DeepSeek--V3-orange.svg)

MedKG 是一个基于 **LLM + KG (知识图谱) 双引擎协同**的闭环医疗数据治理平台。它将大语言模型的语义理解能力与知识图谱的逻辑严谨性进行深度融合，为医疗机构提供从“非结构化政策”到“自动化规则执行”、从“临床口语”到“标准术语编码”的全链路、一站式治理方案。

---

## 🌟 系统核心能力 (System Capabilities)

MedKG v2.4 引入了全新的治理工作流与智能架构，具备以下四大核心技术优势：

### 1. 🎯 自动化政策规则化引擎 (Text-to-SHACL)
- **精准解析**: 自动识别 PDF/Word 政策文件中的报销范围、先行支付比例、性别限制等复杂条件。
- **符号化转换**: 将自然语言规则无损转换为符合 W3C 标准的 **SHACL 约束**，实现对 HIS/LIS 业务数据的毫秒级合规性自动化稽核。

### 2. 🧬 临床 NLP 与术语智能对齐 (Medical NER & Normalization)
- **多维度提取**: 深度集成医疗专用 NLP 引擎，支持对出院小结、检查报告等文本进行高精度实体识别。
- **双模态对齐**: 结合 **Vector Search (向量召回)** 与 **LLM 语义比对**，将非标术语自动对齐至 ICD-10/ICD-11、LONIC、手术码等国家标准编码库。

### 3. 📊 全域知识资产管理中心 (Unified Asset Catalog)
- **图谱驱动**: 系统不再孤立管理数据库表，而是通过“数据血缘 + 医疗本体”双图模式，构建端到端的知识资产地图。
- **质量溯源**: 内置 50+ 项质控巡检规则，实时监控资产健康度，并提供可视化数据流转链路追踪。

### 4. � 增强版可解释决策助手 (GraphRAG v2)
- **多轮对话能力支持**: 基于 **GraphRAG (图增强检索生成)** 技术，提供专业的医保政策咨询。
- **推理过程可视化**: 系统生成的答案附带完整的“推理链路 (Reasoning Trace)”与“政策来源 (Policy Grounding)”，实现 AI 决策的可回溯、可审计。

---

## 🧱 技术架构与目录结构

系统采用**神经符号协同 (Neuro-Symbolic)** 设计，确保前端响应敏捷、后端逻辑严密。

### 核心分层
- **感知层 (NLP/OCR)**: 原始文本与文档的结构化处理。
- **认知层 (LLM + KG)**: 知识获取与逻辑推理的核心。
- **治理层 (Task/Catalog)**: 人机协作及资产的全生命周期监控。

### 目录结构深度解析
```text
MedKG/
├── backend/                # FastAPI 后端核心
│   ├── app/
│   │   ├── api/            # REST API 路由 (auth, catalog, terminology, explanation 等)
│   │   ├── services/       # 核心业务逻辑实现 (服务编排、NLP 引擎)
│   │   ├── core/           # 基础设施配置 (Neo4j, VectorDB, Auth 逻辑)
│   │   └── resources/      # 标准术语库、ICD 样本数据
│   ├── storage/            # 持久化文件与对话历史存储
│   └── main.py             # 启动入口点
├── frontend/               # Vue 3 前端系统
│   └── src/
│       ├── services/       # API 请求封装层
│       ├── views/          # 核心视图 (Home, DataCatalog, NLPWorkbench, Explanation)
│       ├── components/     # 全局复用 UI 组件
└── .env/                   # 环境配置 (API Key, 数据库连接)
```

---

## 🚀 快速启动

### ⚡️ 一键启动脚本
我们提供了快捷启动脚本，可同时管理前后端服务：
```bash
./start.sh start   # 自动激活 medical 环境并启动前后端
```

### 🛠️ 手动部署流程
1. **Neo4j 准备**: 确保 Neo4j 数据库已运行，并正确配置 `.env` 中的 `NEO4J_URI`。
2. **后端 (Conda 环境: medical)**:
   ```bash
   cd backend && pip install -r requirements.txt
   uvicorn app.main:app --port 8001 --reload
   ```
3. **前端 (Node.js 16+)**:
   ```bash
   cd frontend && npm install
   npm run dev
   ```

---

## 🤝 愿景
MedKG 致力于打造医疗领域最专业的“智能体驱动”治理底座。

**License**: MIT