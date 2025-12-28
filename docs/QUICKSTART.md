# 检查项目标准化 - 快速开始指南

## 🚀 5分钟快速启动

### 1. 启动Neo4j (30秒)
```bash
docker-compose -f docker-compose-neo4j.yml up -d
```

### 2. 导入本体数据 (1分钟)
```bash
cd backend
python scripts/import_examination_ontology.py ../examination_ontology.csv --clear
```

### 3. 启动服务 (1分钟)
```bash
# 后端
uvicorn app.main:app --reload

# 前端(新终端)
cd ../frontend
npm run dev
```

### 4. 访问系统 (1分钟)
- 前端: http://localhost:5173
- 后端API: http://localhost:8000/docs
- Neo4j: http://localhost:7474 (neo4j/medkg2024)

### 5. 测试功能 (1分钟)
```bash
cd backend
./scripts/test_examination_e2e.sh
```

---

## 📁 关键文件

| 文件 | 用途 |
|------|------|
| `examination_ontology.csv` | 170+条本体数据 |
| `test_examination_data.csv` | 测试数据 |
| `scripts/import_examination_ontology.py` | 导入脚本 |
| `scripts/test_examination_e2e.sh` | 端到端测试 |

---

## 🔧 常用命令

```bash
# 导入数据
python backend/scripts/import_examination_ontology.py examination_ontology.csv

# 清空并重新导入
python backend/scripts/import_examination_ontology.py examination_ontology.csv --clear

# 运行测试
./backend/scripts/test_examination_e2e.sh

# 查看Neo4j日志
docker logs -f medkg-neo4j

# 重启Neo4j
docker-compose -f docker-compose-neo4j.yml restart
```

---

## ✅ 实施计划完成情况

### Phase 1: 图谱建模与导入 ✅
- [x] 设计图谱Schema
- [x] 实现 `examination_kg_importer.py`
- [x] 实现 `examination_kg_service.py`
- [x] 编写导入脚本 (`import_examination_ontology.py`)

### Phase 2: 服务集成 ✅
- [x] 修改 `examination_standardization_service.py`
- [x] 集成图谱查询到Prompt生成
- [x] 集成图谱验证到结果校验

### Phase 3: API与前端 ✅
- [x] 新增导入/查询API (8个端点)
- [x] 前端树状结构展示
- [x] 测试端到端流程 (`test_examination_e2e.sh`)

---

## 📊 系统架构

```
用户上传CSV
    ↓
标准化服务 ←→ Neo4j图谱 ←→ LLM
    ↓
标准化结果
    ↓
导出Excel/CSV
```

---

完整文档: `walkthrough.md`
