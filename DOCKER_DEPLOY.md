# Docker 一键部署指南

## 🚀 快速开始

### 架构支持

✅ **支持多架构**:
- `linux/amd64` (x86_64) - Intel/AMD 处理器
- `linux/arm64` (ARM) - Apple Silicon M1/M2, ARM 服务器

Docker 会自动检测并使用正确的架构。

### 方法一：使用部署脚本（推荐）

```bash
# 运行部署脚本
./docker-deploy.sh
```

脚本提供交互式菜单：
1. 启动所有服务
2. 停止所有服务
3. 重启所有服务
4. 查看服务状态
5. 查看日志
6. 重新构建并启动
7. 清理所有数据

### 方法二：手动执行

```bash
# 1. 准备配置文件
cp config/.env.example config/.env
vim config/.env  # 填入 API Keys

# 2. 启动所有服务（自动检测架构）
docker-compose up -d

# 或指定架构
DOCKER_PLATFORM=linux/amd64 docker-compose up -d  # AMD64
DOCKER_PLATFORM=linux/arm64 docker-compose up -d  # ARM64

# 3. 查看日志
docker-compose logs -f

# 4. 停止服务
docker-compose down
```

### 方法三：多架构构建（高级）

```bash
# 使用 buildx 构建多架构镜像
./docker/build-multiarch.sh

# 选项：
#   1) 当前平台
#   2) AMD64 only
#   3) ARM64 only
#   4) 同时构建 AMD64 + ARM64
```

## 📦 服务说明

### 端口配置

| 服务 | 容器端口 | 主机端口 | 说明 |
|------|----------|----------|------|
| Frontend | 8042 | 8042 | React 前端界面（唯一对外端口） |
| Backend | 8043 | - | FastAPI 后端（仅 Docker 内网） |
| Weaviate | 8080 | - | 向量数据库（仅 Docker 内网） |
| Scheduler | - | - | 后台定时任务 |

**安全设计**：
- 只有前端 8042 端口暴露到公网
- 后端 API 和 Weaviate 只在 Docker 内网通信
- 所有 API 请求通过 Nginx 代理转发
- 避免端口冲突和安全风险

### 访问地址

- **前端界面**: http://localhost:8042
- **后端 API**: http://localhost:8042/api（通过 Nginx 代理）
- **API 文档**: http://localhost:8042/api/docs（通过 Nginx 代理）

**注意**：Weaviate 和后端 API 不再直接暴露，只能通过前端端口访问。

## ⚙️ 配置说明

### 环境变量 (config/.env)

```env
# OpenAI API (通过 LiteLLM 代理)
OPENAI_API_KEY=sk-xxx

# TopHub API
TOPHUB_API_KEY=xxx

# Weaviate 配置（可选，默认使用 Docker 内部服务）
WEAVIATE_URL=http://weaviate:8080
```

### 指定架构

默认自动检测架构，也可以手动指定：

**方式 1: 环境变量**
```bash
# AMD64 (x86_64)
export DOCKER_PLATFORM=linux/amd64
docker-compose up -d

# ARM64
export DOCKER_PLATFORM=linux/arm64
docker-compose up -d
```

**方式 2: .env.docker 文件**
```bash
# 复制配置模板
cp .env.docker.example .env.docker

# 编辑配置
vim .env.docker
# 设置: DOCKER_PLATFORM=linux/amd64 或 linux/arm64

# 加载配置启动
docker-compose --env-file .env.docker up -d
```

### 修改端口

编辑 `docker-compose.yml`：

```yaml
services:
  frontend:
    ports:
      - "8042:8042"  # 改为其他端口，如 "9000:8042"

  backend:
    ports:
      - "8043:8043"  # 改为其他端口，如 "9001:8043"
```

## 📊 数据持久化

以下目录挂载到主机，数据会保留：

```
./config    - 任务配置、schedule 文件
./logs      - 日志文件
./output    - 生成的 Markdown 摘要
./data      - 缓存数据
```

Weaviate 数据存储在 Docker Volume `weaviate_data`。

## 🔧 常用命令

### 查看服务状态

```bash
docker-compose ps
```

### 查看日志

```bash
# 所有服务
docker-compose logs -f

# 特定服务
docker-compose logs -f backend
docker-compose logs -f scheduler
docker-compose logs -f frontend
```

### 重启服务

```bash
# 重启所有
docker-compose restart

# 重启特定服务
docker-compose restart backend
```

### 进入容器

```bash
# 进入后端容器
docker-compose exec backend bash

# 进入守护进程容器
docker-compose exec scheduler bash
```

### 重新构建

```bash
# 代码更新后重新构建
docker-compose down
docker-compose up -d --build

# 强制无缓存重建
docker-compose build --no-cache
docker-compose up -d
```

## 🌐 远程服务器部署

### 1. 复制项目到服务器

```bash
# 使用 rsync
rsync -avz --exclude 'node_modules' --exclude '__pycache__' \
  ./ user@server:/path/to/news2context/

# 或使用 git
git clone https://github.com/your-org/news2context.git
cd news2context
```

### 2. 配置环境

```bash
cp config/.env.example config/.env
vim config/.env  # 填入配置
```

### 3. 启动服务

```bash
docker-compose up -d
```

### 4. 配置反向代理（可选）

使用 Nginx 或 Traefik 配置域名和 HTTPS：

```nginx
# /etc/nginx/sites-available/news2context
server {
    listen 80;
    server_name news.example.com;

    location / {
        proxy_pass http://localhost:8042;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 80;
    server_name api.news.example.com;

    location / {
        proxy_pass http://localhost:8043;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🐛 故障排查

### 前端无法访问

```bash
# 检查容器状态
docker-compose ps frontend

# 查看日志
docker-compose logs frontend

# 检查 Nginx 配置
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf
```

### 后端 API 错误

```bash
# 查看后端日志
docker-compose logs backend

# 检查环境变量
docker-compose exec backend env | grep API_KEY

# 检查 Weaviate 连接
docker-compose exec backend curl http://weaviate:8080/v1/.well-known/ready
```

### Weaviate 无法连接

```bash
# 检查 Weaviate 状态
docker-compose ps weaviate

# 测试连接
curl http://localhost:8080/v1/.well-known/ready

# 查看日志
docker-compose logs weaviate
```

### 定时任务不执行

```bash
# 查看 scheduler 日志
docker-compose logs scheduler

# 检查任务配置
cat config/schedules/ceo-news.yaml
```

## 💾 备份与恢复

### 备份

```bash
# 备份配置和数据
tar czf backup-$(date +%Y%m%d).tar.gz config/ logs/ output/ data/

# 备份 Weaviate 数据
docker run --rm \
  -v news2context_weaviate_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/weaviate-$(date +%Y%m%d).tar.gz /data
```

### 恢复

```bash
# 恢复配置和数据
tar xzf backup-YYYYMMDD.tar.gz

# 恢复 Weaviate
docker run --rm \
  -v news2context_weaviate_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/weaviate-YYYYMMDD.tar.gz -C /
```

## 📈 性能优化

### 资源限制

在 `docker-compose.yml` 中添加：

```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
      reservations:
        cpus: '1'
        memory: 512M
```

### 日志轮转

```yaml
backend:
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
```

## 🔒 安全建议

1. **不要提交 `.env` 文件到 Git**
2. **使用强密码**（如果配置了数据库认证）
3. **配置防火墙**：只开放必要端口
4. **使用 HTTPS**：生产环境配置 SSL 证书
5. **定期更新镜像**：`docker-compose pull && docker-compose up -d`

## 📚 更多文档

- 详细部署文档：[docker/README.md](docker/README.md)
- 项目架构：[CLAUDE.md](CLAUDE.md)
- 主文档：[README.md](README.md)

## 🆘 获取帮助

如遇问题，请查看：
1. 日志文件：`docker-compose logs -f`
2. 容器状态：`docker-compose ps`
3. 资源使用：`docker stats`
4. GitHub Issues
