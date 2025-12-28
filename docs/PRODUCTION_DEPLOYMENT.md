# 生产部署指南 (Production Deployment Guide)

## 1. 环境准备

### 1.1 服务器要求
- **CPU**: 4核心以上
- **内存**: 8GB以上
- **存储**: 100GB SSD
- **操作系统**: Ubuntu 22.04 LTS / CentOS 8

### 1.2 必需软件
```bash
# Docker & Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

---

## 2. 数据库部署

### 2.1 启动数据库服务
```bash
docker-compose up -d neo4j postgres milvus
```

### 2.2 初始化数据库
```bash
# Neo4j 初始化
docker exec -it medical_neo4j cypher-shell -u neo4j -p password < init_neo4j.cypher

# PostgreSQL 初始化
docker exec -it medical_postgres psql -U medical_user -d medical_governance < init_postgres.sql
```

---

## 3. 后端部署

### 3.1 环境变量配置
创建 `.env` 文件：
```bash
# Security
SECRET_KEY=your-production-secret-key-min-32-chars
ALGORITHM=HS256

# Database
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password

POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=medical_user
POSTGRES_PASSWORD=your-postgres-password
POSTGRES_DB=medical_governance

MILVUS_HOST=milvus
MILVUS_PORT=19530

# LLM API (替换为真实API)
OPENAI_API_KEY=sk-your-openai-key
# 或使用其他LLM
ANTHROPIC_API_KEY=sk-ant-your-key
```

### 3.2 Docker部署
```bash
# 构建镜像
cd backend
docker build -t medical-governance/backend:v1.0 .

# 运行容器
docker run -d \
  --name medical-backend \
  --env-file .env \
  -p 8000:8000 \
  --network medical-network \
  medical-governance/backend:v1.0
```

### 3.3 使用 Docker Compose
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  backend:
    image: medical-governance/backend:v1.0
    env_file: .env
    ports:
      - "8000:8000"
    depends_on:
      - neo4j
      - postgres
      - milvus
    restart: unless-stopped
```

---

## 4. 前端部署

### 4.1 构建生产版本
```bash
cd frontend
npm run build
```

### 4.2 Docker部署
```bash
docker build -t medical-governance/frontend:v1.0 .

docker run -d \
  --name medical-frontend \
  -p 80:80 \
  medical-governance/frontend:v1.0
```

---

## 5. 安全加固

### 5.1 HTTPS配置 (使用Let's Encrypt)
```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com
```

### 5.2 防火墙配置
```bash
# 只开放必要端口
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

### 5.3 环境变量加密
使用 Docker Secrets 或 Kubernetes Secrets 管理敏感信息。

---

## 6. 监控与日志

### 6.1 日志收集
```bash
# 查看后端日志
docker logs -f medical-backend

# 持久化日志
docker run -v /var/log/medical:/app/logs ...
```

### 6.2 监控指标
推荐使用 Prometheus + Grafana:
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'medical-backend'
    static_configs:
      - targets: ['backend:8000']
```

---

## 7. 性能优化

### 7.1 数据库连接池
```python
# 在 config.py 中配置
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 10
```

### 7.2 缓存策略
```python
# 使用 Redis 缓存术语映射结果
REDIS_URL = "redis://redis:6379/0"
CACHE_TTL = 3600  # 1小时
```

### 7.3 负载均衡
使用 Nginx 或 Traefik 进行负载均衡：
```nginx
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}
```

---

## 8. 备份策略

### 8.1 数据库备份
```bash
# Neo4j 备份
docker exec medical_neo4j neo4j-admin backup --backup-dir=/backups

# PostgreSQL 备份
docker exec medical_postgres pg_dump -U medical_user medical_governance > backup.sql
```

### 8.2 自动备份脚本
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
docker exec medical_postgres pg_dump -U medical_user medical_governance > /backups/pg_$DATE.sql
docker exec medical_neo4j neo4j-admin backup --backup-dir=/backups/neo4j_$DATE

# 保留最近7天的备份
find /backups -mtime +7 -delete
```

---

## 9. 故障排查

### 9.1 常见问题

**问题**: 后端无法连接数据库
```bash
# 检查网络
docker network inspect medical-network

# 检查数据库状态
docker ps | grep neo4j
```

**问题**: LLM API超时
```python
# 增加超时时间
OPENAI_TIMEOUT = 60  # 秒
```

### 9.2 健康检查
```bash
# 检查后端健康状态
curl http://localhost:8000/health

# 检查数据库连接
curl http://localhost:8000/api/v1/health/db
```

---

## 10. 扩展部署 (Kubernetes)

### 10.1 Deployment 配置
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: medical-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: medical-backend
  template:
    metadata:
      labels:
        app: medical-backend
    spec:
      containers:
      - name: backend
        image: medical-governance/backend:v1.0
        ports:
        - containerPort: 8000
        env:
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: medical-secrets
              key: secret-key
```

---

## 附录：生产检查清单

- [ ] 所有密钥已更换为生产密钥
- [ ] HTTPS已配置
- [ ] 防火墙已启用
- [ ] 日志已配置
- [ ] 监控已部署
- [ ] 备份脚本已设置
- [ ] 负载测试已完成
- [ ] 灾难恢复计划已制定
