# 医疗知识图谱术语与规则治理工具

## 快速开始

### 1. 启动基础设施
```bash
docker-compose up -d
```

这将启动：
- **Neo4j** (图数据库): http://localhost:7474
- **PostgreSQL** (关系数据库): localhost:5432
- **Milvus** (向量数据库): localhost:19530

### 2. 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

### 3. 启动API服务
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API文档: http://localhost:8000/docs

## 核心功能

### 1. 数据接入 (Ingestion)
上传医保政策文档（PDF/TXT）并自动解析切片。

```bash
curl -X POST "http://localhost:8000/api/v1/ingest/document" \
  -F "file=@policy.pdf"
```

### 2. 术语标准化 (Terminology Normalization)
将临床术语映射到标准医保编码。

```bash
curl -X POST "http://localhost:8000/api/v1/terminology/normalize" \
  -H "Content-Type: application/json" \
  -d '{"terms": ["二型糖伴酮症", "高血压"]}'
```

### 3. 规则编译 (Rule Compilation)
将自然语言政策转换为SHACL规则。

```bash
curl -X POST "http://localhost:8000/api/v1/rules/compile" \
  -H "Content-Type: application/json" \
  -d '{"policy_text": "门诊透析每日限额400元"}'
```

## 项目结构

```
backend/
├── app/
│   ├── api/              # API路由
│   ├── core/             # 核心接口定义
│   ├── services/         # 业务逻辑
│   ├── adapters/         # 外部系统适配器
│   ├── plugins/          # 可插拔解析器
│   └── templates/        # SHACL模板
├── requirements.txt
└── main.py
```

## 扩展性设计

### 添加新的规则解析器
1. 继承 `RuleParserPlugin`
2. 实现 `can_handle()` 和 `parse()` 方法
3. 在 `RuleCompiler` 中注册

### 切换LLM提供商
实现 `LLMProvider` 接口，替换 `MockLLMProvider`。

## 下一步开发
- [ ] 实现GraphRAG解释服务
- [ ] 集成真实的LLM API (OpenAI/Claude)
- [ ] 实现向量数据库真实连接
- [ ] 添加用户认证
