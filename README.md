# MedKG: 医疗知识图谱术语与规则治理平台

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Vite](https://img.shields.io/badge/frontend-Vue3-green.svg)
![FastAPI](https://img.shields.io/badge/backend-FastAPI-blue.svg)
![Neo4j](https://img.shields.io/badge/database-Neo4j-red.svg)

MedKG 是一个基于 **LLM + KG (知识图谱) 双引擎协同**的高端医疗数据治理平台。它将大语言模型的语义理解能力与知识图谱的逻辑严谨性相结合，为医疗机构提供从政策解析到规则执行、从模糊术语到标准编码的全链路治理方案。

---

## 🌟 系统核心能力

MedKG 不仅仅是一个工具，而是一个完整的智能体驱动治理框架，具备以下核心能力：

- **🎯 政策规则化自动化 (Text-to-Rule)**: 革命性地改变了传统人工输入规则的模式。系统能自动解析 PDF/Word 格式的医保政策文档，将其重构为逻辑严谨的 SHACL 约束规则，支持对门诊、住院、药耗等多场景规则的自动提取。
- **🧬 语义化术语自动对齐**: 解决医疗行业“多名一指”的痛点。通过向量召回初步定位候选，再利用 LLM 对临床黑话进行深层语义比对，实现与国家标准医保编码（ICD-10/ICD-11）的高精度映射。
- **📊 知识驱动的决策解释 (GraphRAG)**: 当发生医保拒付时，系统不再给出笼统的错误代码，而是通过 GraphRAG 技术串联“患者诊断 -> 触发规则 -> 政策依据”，生成可追溯、可审计的自然语言解释报告。
- **� 动态治理与版本演化**: 系统具备感知政策变动的能力。通过本体演化 Agent 监控规则冲突，并提供沙箱环境进行历史数据回测，确保新旧规则平稳过渡。

---

## 🧱 模块化架构

系统由四个核心服务模块组成，通过标准 REST API 实现松耦合协作：

### 1. Ingestion Service (数据接入模块)
- **职责**: 负责多模态数据的预处理。
- **技术**: 支持长文本切片的语义索引（Semantic Chunking）和 OCR 解析。

### 2. Terminology Service (术语治理模块)
- **职责**: 管理本体映射逻辑。
- **特性**: 包含 Few-shot 示例库管理、人工审核工作台（Human-in-the-loop）和术语质量评估引擎。

### 3. Rules Compiler (规则编译模块)
- **职责**: 自然语言到代码的转译。
- **架构**: 采用基于插件的解析器架构（Parser Plugin Architecture），支持向 SHACL、Cypher、SPARQL 等多种目标语言编译。

### 4. Explanation Service (解释增强服务)
- **职责**: 提供基于图谱的 RAG 服务。
- **功能**: 计算子图相似度，构建证据链，并利用 LLM 汇总生成最终的咨询响应。

---

## 🏛️ 框架结构与分层设计

本系统采用**神经符号驱动的层级化设计**，确保既有灵活性又有可靠性。

### 技术路线图
- **接入层 (Multi-modal Ingestion)**: 对接全量医疗政策与诊疗数据。
- **神经符号协同层 (Neuro-Symbolic Layer)**: 
    - **快思考 (Neural)**: LLM 负责语义解析与生成草案。
    - **慢思考 (Symbolic)**: KG 负责本体校验 (SHACL) 与严谨推理。
- **治理层 (Dynamic Governance)**: 监控规则冲突与版本演化。
- **应用服务层 (Service Layer)**: 提供 Copilot、审核工作台等终端接口。

### 目录结构深度解析
```text
MedKG/
├── backend/                # 后端核心
│   ├── app/
│   │   ├── api/            # 暴露给前端的 REST API 路由
│   │   ├── services/       # 业务逻辑编排 (核心模块实现)
│   │   ├── core/           # 接口基类、模型定义与公共配置
│   │   ├── plugins/        # 规则解析器插件扩展目录
│   │   └── templates/      # 预置的 SHACL 规则模板
│   ├── storage/            # 临时与持久化文件存储
│   └── main.py             # FastAPI 启动入口
├── frontend/               # 前端系统
│   └── src/
│       ├── components/     # UI 基础组件
│       ├── views/          # 业务页面 (治理台、审核、问答)
│       └── store/          # 全局状态管理
└── infra/                  # 基础设施配置 (docker-compose 等)
```

---

## 🚀 快速开始

### 1. 基础设施启动
```bash
docker-compose up -d
```

### 2. 后端服务初始化 (需要 Python 3.9+)
```bash
cd backend
pip install -r requirements.txt
python verify_core_modules.py  # 验证核心模块可用性
uvicorn app.main:app --reload
```

### 3. 前端界面启动
```bash
cd frontend
npm install
npm run dev
```

---

## 🤝 贡献与反馈
我们致力于打造最专业的医疗治理底座。如果您有任何建议或发现 Bug，请通过 Issue 提交。

**License**: MIT