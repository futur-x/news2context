# Docker 部署指南

## 快速启动

### 1. 准备配置文件

```bash
# 复制环境变量配置
cp config/.env.example config/.env

# 编辑配置文件，填入必要的 API Keys
vim config/.env
```

### 2. 启动所有服务

```bash
# 构建并启动所有容器
docker-compose up -d

# 查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f scheduler
```

### 3. 访问服务

- **前端界面**: http://localhost:8042
- **后端 API**: http://localhost:8043
- **API 文档**: http://localhost:8043/docs
- **Weaviate**: http://localhost:8080

### 4. 停止服务

```bash
# 停止所有容器
docker-compose down

# 停止并删除数据卷（警告：会删除所有数据）
docker-compose down -v
```

## 服务说明

### 服务架构

```
┌─────────────────────────────────────────┐
│  Frontend (Nginx)                       │
│  Port: 8042                             │
│  - React SPA                            │
│  - API Proxy to Backend                 │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  Backend API (FastAPI)                  │
│  Port: 8043                             │
│  - REST API                             │
│  - Task Management                      │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
┌───────▼────────┐  ┌──────▼──────────────┐
│  Scheduler     │  │  Weaviate Database  │
│  (APScheduler) │  │  Port: 8080         │
│  - Cron Jobs   │  │  - Vector Store     │
└────────────────┘  └─────────────────────┘
```

### 容器列表

| 容器名 | 服务 | 端口 | 说明 |
|--------|------|------|------|
| news2context-frontend | 前端 | 8042 | React + Nginx |
| news2context-backend | 后端 | 8043 | FastAPI API 服务 |
| news2context-scheduler | 守护进程 | - | 定时任务调度 |
| news2context-weaviate | 数据库 | 8080 | 向量数据库 |

## 配置说明

### 端口配置

在 `docker-compose.yml` 中修改端口映射：

```yaml
services:
  frontend:
    ports:
      - "8042:8042"  # 主机端口:容器端口

  backend:
    ports:
      - "8043:8043"
```

### 环境变量

在 `config/.env` 中配置：

```env
# OpenAI API (通过 LiteLLM)
OPENAI_API_KEY=sk-xxx

# TopHub API
TOPHUB_API_KEY=xxx

# Weaviate (可选)
WEAVIATE_URL=http://weaviate:8080
```

### 数据持久化

以下目录会挂载到宿主机：

- `./config` - 配置文件（任务配置、schedule）
- `./logs` - 日志文件
- `./output` - 生成的 Markdown 摘要
- `./data` - 缓存数据

Weaviate 数据存储在 Docker Volume `weaviate_data` 中。

## 常用命令

### 查看服务状态

```bash
docker-compose ps
```

### 重启特定服务

```bash
docker-compose restart backend
docker-compose restart scheduler
```

### 查看实时日志

```bash
# 所有服务
docker-compose logs -f

# 特定服务
docker-compose logs -f backend
docker-compose logs -f scheduler
```

### 进入容器调试

```bash
# 进入后端容器
docker-compose exec backend bash

# 进入守护进程容器
docker-compose exec scheduler bash
```

### 重新构建镜像

```bash
# 重新构建所有镜像
docker-compose build

# 重新构建特定服务
docker-compose build backend

# 无缓存重建
docker-compose build --no-cache
```

### 更新代码后重启

```bash
# 停止服务
docker-compose down

# 重新构建并启动
docker-compose up -d --build
```

## 故障排查

### 1. 前端无法访问

检查前端日志：
```bash
docker-compose logs frontend
```

确认 Nginx 配置是否正确。

### 2. 后端 API 报错

检查后端日志：
```bash
docker-compose logs backend
```

确认配置文件 `config/.env` 是否正确。

### 3. Weaviate 连接失败

检查 Weaviate 是否启动：
```bash
docker-compose ps weaviate
curl http://localhost:8080/v1/.well-known/ready
```

### 4. 定时任务不执行

检查 scheduler 日志：
```bash
docker-compose logs scheduler
```

确认任务配置文件 `config/schedules/*.yaml` 中的 `enabled: true`。

### 5. 查看容器资源使用

```bash
docker stats
```

## 生产环境部署

### 1. 使用外部数据库（推荐）

修改 `docker-compose.yml`，移除 weaviate 服务，在 backend 中配置外部 Weaviate 地址：

```yaml
backend:
  environment:
    - WEAVIATE_URL=http://your-weaviate-host:8080
```

### 2. 使用反向代理（Nginx/Traefik）

```nginx
# 前端
server {
    listen 80;
    server_name news2context.example.com;

    location / {
        proxy_pass http://localhost:8042;
    }
}

# 后端 API
server {
    listen 80;
    server_name api.news2context.example.com;

    location / {
        proxy_pass http://localhost:8043;
    }
}
```

### 3. 启用 HTTPS

使用 Let's Encrypt 或其他 SSL 证书。

### 4. 资源限制

在 `docker-compose.yml` 中添加资源限制：

```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
      reservations:
        cpus: '1'
        memory: 1G
```

## 备份与恢复

### 备份 Weaviate 数据

```bash
# 备份数据卷
docker run --rm \
  -v news2context_weaviate_data:/data \
  -v $(pwd)/backup:/backup \
  alpine tar czf /backup/weaviate-backup-$(date +%Y%m%d).tar.gz /data
```

### 恢复 Weaviate 数据

```bash
# 停止服务
docker-compose down

# 恢复数据
docker run --rm \
  -v news2context_weaviate_data:/data \
  -v $(pwd)/backup:/backup \
  alpine tar xzf /backup/weaviate-backup-YYYYMMDD.tar.gz -C /

# 启动服务
docker-compose up -d
```

### 备份配置和输出

```bash
tar czf news2context-config-$(date +%Y%m%d).tar.gz \
  config/ logs/ output/ data/
```

## 监控

### 健康检查

所有服务都配置了健康检查，可以通过以下命令查看：

```bash
docker-compose ps
```

### 日志轮转

建议配置日志轮转防止日志文件过大：

```yaml
backend:
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
```

## 更新指南

### 拉取最新代码

```bash
git pull origin main
docker-compose down
docker-compose up -d --build
```

### 数据库迁移

如果有 schema 变更，需要重建 Weaviate 数据（会丢失数据）：

```bash
docker-compose down -v
docker-compose up -d
```
