# Mock 清理计划

## 需要移除的 Mock 实现

### 1. Schema Service ✅ (已完成)

- **文件**: `backend/app/services/schema_service.py`
- **状态**: 已使用真实的 knext SDK
- **Mock 代码**: 已移除,使用 SchemaClient

### 2. Graph Service (需要更新)

- **文件**: `backend/app/services/graph_service.py`
- **当前**: 使用 mock GraphStorage
- **需要**: 使用真实的 KAG GraphStorage
- **依赖**: openspg-kag 已安装

### 3. Clinical NLP Service (需要配置)

- **文件**: `backend/app/services/clinical_nlp_service.py`
- **当前**: 使用 MockLLMProvider
- **需要**: 使用真实的 LLM (已在 kag_config.yaml 配置)
- **操作**: 替换为 KAG LLM client

### 4. Enhanced Ingest Service (需要配置)

- **文件**: `backend/app/services/enhanced_ingest_service.py`
- **当前**: 使用 Mock DeepKE
- **需要**: 使用 KAG 的 SchemaFreeExtractor
- **操作**: 集成 KAG builder

### 5. Terminology Service (外部依赖)

- **文件**: `backend/app/services/terminology_service.py`
- **当前**: Mock MedCT/MedLink
- **需要**: 真实的医学术语服务 API
- **注意**: 需要外部服务配置

### 6. Vector Terminology Service (需要配置)

- **文件**: `backend/app/services/vector_terminology_service.py`
- **当前**: MockLLMProvider
- **需要**: 使用 KAG LLM
- **操作**: 替换为真实 LLM

### 7. Rule Service (需要配置)

- **文件**: `backend/app/services/rule_service.py`
- **当前**: MockLLMProvider
- **需要**: 使用 KAG LLM
- **操作**: 替换为真实 LLM

### 8. Search Service (需要实现)

- **文件**: `backend/app/services/search_service.py`
- **当前**: Mock retrieval
- **需要**: 使用 KAG solver 的检索功能
- **操作**: 集成 KAG hybrid retrieval

### 9. Data Governance Service (业务逻辑)

- **文件**: `backend/app/services/data_governance_service.py`
- **当前**: Mock HIS 数据库扫描
- **需要**: 真实的数据库连接
- **注意**: 需要 HIS 系统访问权限

### 10. Sandbox Service (业务逻辑)

- **文件**: `backend/app/services/sandbox_service.py`
- **当前**: Mock SHACL 验证
- **需要**: 真实的 SHACL 引擎
- **操作**: 集成 RDFLib + pySHACL

## 优先级

### 高优先级 (立即处理)

1. ✅ Schema Service - 已完成
2. Graph Service - 使用 KAG GraphStorage
3. Clinical NLP Service - 使用 KAG LLM
4. Enhanced Ingest Service - 使用 KAG Builder
5. Search Service - 使用 KAG Solver

### 中优先级 (需要配置)

6. Vector Terminology Service - 使用 KAG LLM
7. Rule Service - 使用 KAG LLM

### 低优先级 (需要外部服务)

8. Terminology Service - 需要 MedCT/MedLink API
9. Data Governance Service - 需要 HIS 系统
10. Sandbox Service - 需要 SHACL 引擎

## 实施步骤

1. 移除所有 MockLLMProvider,统一使用 KAG LLM
2. 移除 Graph Service 的 mock,使用真实 GraphStorage
3. 集成 KAG Builder 到 Enhanced Ingest Service
4. 集成 KAG Solver 到 Search Service
5. 为需要外部服务的功能添加配置说明
