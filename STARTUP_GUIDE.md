# 医疗知识图谱治理工具 - 启动指南

## 快速启动

### 1. 启动后端服务

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动API服务
uvicorn app.main:app --reload --port 8000
```

后端API文档: http://localhost:8000/docs

### 2. 启动前端服务

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端界面: http://localhost:3000

### 3. (可选) 启动数据库

```bash
# 在项目根目录
docker-compose up -d
```

这将启动 Neo4j, PostgreSQL, Milvus 等数据库服务。

---

## 功能演示

### 政策上传页面
1. 访问 http://localhost:3000/upload
2. 拖拽或选择PDF/TXT政策文件
3. 点击"开始上传"
4. 查看解析结果（字符数、切片数量）

### 规则审核页面
1. 访问 http://localhost:3000/rules
2. 输入自然语言政策（如："门诊透析每日限额400元"）
3. 点击"编译为SHACL规则"
4. 查看生成的SHACL代码
5. 点击"在沙箱中测试"查看回测结果

### 术语清洗工作台
1. 访问 http://localhost:3000/terminology
2. 输入临床术语（如："二型糖伴酮症"）
3. 点击"标准化"
4. 查看映射结果和匹配理由
5. 对结果进行"通过"或"拒绝"审核

### 拒付解释查询
1. 访问 http://localhost:3000/explanation
2. 输入患者ID（如："P001"）
3. 查看证据链和自然语言解释
4. 或切换到"政策问答"标签进行问答

---

## API端点列表

### 数据接入
- `POST /api/v1/ingest/document` - 上传政策文档

### 术语治理
- `POST /api/v1/terminology/normalize` - 术语标准化
- `POST /api/v1/terminology/feedback` - 提交人工审核反馈

### 规则管理
- `POST /api/v1/rules/compile` - 编译自然语言为SHACL
- `POST /api/v1/rules/test` - 沙箱测试规则

### 解释服务
- `GET /api/v1/explanation/rejection/{patient_id}` - 拒付原因解释
- `POST /api/v1/explanation/query` - 政策问答

---

## 项目结构

```
治理工具/
├── backend/                 # FastAPI后端
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── core/           # 核心接口和配置
│   │   ├── services/       # 业务逻辑
│   │   ├── adapters/       # 数据库适配器
│   │   ├── plugins/        # 规则解析插件
│   │   └── templates/      # SHACL模板
│   └── requirements.txt
├── frontend/                # Vue 3前端
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   ├── services/       # API服务
│   │   └── App.vue
│   └── package.json
└── docker-compose.yml       # 数据库服务
```

---

## 注意事项

1. **Mock模式**: 当前使用Mock适配器，LLM和数据库调用都是模拟的
2. **生产部署**: 需要替换为真实的LLM API和数据库连接
3. **端口配置**: 
   - 后端: 8000
   - 前端: 3000
   - Neo4j: 7474 (HTTP), 7687 (Bolt)
   - PostgreSQL: 5432
   - Milvus: 19530
