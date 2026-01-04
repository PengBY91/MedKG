# MedKG 重构计划：集成 KAG 框架

**版本**: 1.0  
**日期**: 2026-01-04  
**状态**: 规划中

## 1. 项目目标 (Goals)

本项目的核心目标利用 **KAG (Knowledge Augmented Generation)** 框架的能力，全面重构 MedKG 的底层知识引擎。

- **构建升级 (Construction)**: 从由简单的脚本式导入升级为基于 **KAG-Builder** 的流水线构建，支持 PDF/Word 等非结构化文档的自动化抽取、Schema 约束校验及语义对齐。
- **推理升级 (Reasoning)**: 从基础的检索增强 (RAG) 升级为 **KAG-Solver** 驱动的逻辑推理，支持多跳问答、合规性检查（Logic Form）及溯源追踪。
- **架构统一 (Architecture)**: 统一配置管理，通过 `kag_config.yaml` 集中管理 LLM、向量、图存储及流水线参数，降低运维复杂度。

## 2. 工作内容 (Content)

### 2.1 环境与基础设施

- **依赖管理**: 将 `openspg-kag` 引入 Python 环境。
- **配置中心**: 创建并配置 `kag_config.yaml`，对接 OpenSPG Server (GraphStore)、Neo4j 和 Milvus。

### 2.2 模块重构

| 模块         | 当前状态                                   | 重构方案                                                                | 对应 KAG 组件                |
| :----------- | :----------------------------------------- | :---------------------------------------------------------------------- | :--------------------------- |
| **知识构建** | 简单的 Neo4j 写入 (`graph_service.py`)     | 引入 `KAGMedicalBuilder`，实现标准化的 `UnstructuredBuilderChain`。     | `kag.builder.runner`         |
| **逻辑推理** | 模拟/简易 Solver (`kag_solver_service.py`) | 引入 `SolverMain`，配置 `kag_static_pipeline`，支持混合检索与逻辑推演。 | `kag.solver.main_solver`     |
| **图谱存储** | 直接操作 Neo4j Driver                      | 通过 KAG SDK 进行图操作，支持互索引（Chunk-Node 链接）。                | `openspg.api`, `kag.storage` |

### 2.3 关键交付物

1.  `kag_config.yaml`: 核心配置文件。
2.  `backend/app/services/kag_medical_builder.py`: 新增的医疗知识构建服务。
3.  `backend/app/services/kag_solver_service.py`: 重构后的推理服务。
4.  `backend/app/services/graph_service.py`: 适配后的图谱服务。

## 3. 实施计划 (Plan)

### 阶段一：环境准备与配置 (Phase 1: Setup)

- [ ] 在 conda medical 环境中安装 `openspg-kag`。
- [ ] 在项目根目录创建 `kag_config.yaml`。
- [ ] 配置 OpenAI/LLM 凭证及 OpenSPG 连接信息。
- [ ] 验证 KAG SDK 是否能成功加载配置。

### 阶段二：重构知识构建模块 (Phase 2: Builder Refactor)

- [ ] 创建 `kag_medical_builder.py`。
- [ ] 实现 `build_document` 方法，封装 `DefaultUnstructuredBuilderChain`。
- [ ] 配置 Schema 约束抽取器 (`SchemaConstraintExtractor`)，对接 MedKG 现有的 Schema 定义。
- [ ] 编写单元测试：上传一份测试 PDF，验证 Neo4j 中是否生成了正确的实体和 `MENTIONS` 边。

### 阶段三：重构逻辑推理模块 (Phase 3: Solver Refactor)

- [ ] 修改 `kag_solver_service.py`。
- [ ] 初始化 `SolverMain`。
- [ ] 实现 `solve` 接口，对接前端 API。
- [ ] 配置 `kag_solver_pipeline`，启用 `kag_hybrid_retrieval_executor` (混合检索)。
- [ ] 验证：使用测试问题进行提问，检查日志中的推理 Trace 和最终答案。

### 阶段四：集成验证与清理 (Phase 4: Validation & Cleanup)

- [ ] 全链路联调：上传文档 -> 构建图谱 -> 提问回答。
- [ ] 移除旧的 Mock 代码和不再使用的直接 Neo4j 操作代码。
- [ ] 更新 `README.md` 和部署文档。

## 4. 风险与对策

- **Schema 兼容性**: KAG 强依赖 OpenSPG Schema。需确保 MedKG 现有的 Schema 能通过 `schema_service.py` 正确同步到 OpenSPG Server。
- **LLM 成本**: KAG 构建过程涉及多次 LLM 调用。开发阶段建议使用小模型或 Mock LLM 进行流程跑通。

---

集成过程中需要参考的资料:

- `KAG_Developer_Manual.md`
- `KAG_Integration_Guide.md`
