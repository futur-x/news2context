# News2Context v2.0

AI 驱动的智能新闻聚合系统，支持多任务隔离、CLI Agent 交互、REST API 和定时调度。

## ✨ 核心特性

- 🤖 **AI Agent 场景分析** - 根据用户角色智能推荐新闻源
- 📋 **多任务隔离** - 每个任务独立数据库，配置锁定
- 🔌 **插件化引擎** - 支持多种新闻源（TopHub、NewsAPI、RSS...）
- 💻 **CLI 交互界面** - 友好的命令行交互体验
- 🌐 **REST API 服务** - 支持外部系统调用
- ⏰ **定时任务调度** - 自动化新闻采集
- 🗄️ **向量数据库** - Weaviate 语义搜索

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置系统

1. 复制配置模板：
```bash
cp config/.env.example config/.env
```

2. 编辑 `config/.env`，填入 API Keys：
```env
OPENAI_API_KEY=sk-your-openai-key
TOPHUB_API_KEY=your-tophub-key
```

3. 验证配置：
```bash
python test_infrastructure.py
```

### 基本使用（v2.0 开发中）

```bash
# 交互式采集
news2context collect

# 问答查询
news2context chat

# 创建定时任务
news2context schedule create

# 启动后台服务
news2context daemon start
```

## 📖 文档

- [实施方案](docs/implementation_plan.md)
- [开发任务](docs/task.md)
- [API 文档](docs/api.md)（开发中）

## 🏗️ 项目结构

```
news2context/
├── config/              # 配置文件
├── src/
│   ├── cli/            # CLI 命令
│   ├── core/           # 核心业务
│   ├── engines/        # 新闻源引擎
│   ├── api/            # REST API
│   ├── scheduler/      # 定时任务
│   ├── storage/        # 数据存储
│   └── utils/          # 工具模块
├── logs/               # 日志文件
└── data/               # 数据文件
```

## 🔧 开发状态

- ✅ **v1.0**: 基础新闻爬取功能
- 🚧 **v2.0**: 正在开发中
  - ✅ Phase 1: 基础架构（70% 完成）
  - ⏳ Phase 2: 任务管理系统
  - ⏳ Phase 3-8: 待开始

## 📝 更新日志

### v2.0.0-alpha (2025-11-26)

**Phase 1: 基础架构重构**
- ✅ 新目录结构
- ✅ 配置系统（YAML + 环境变量）
- ✅ 插件化引擎架构
- ✅ TopHub 引擎实现
- ✅ 引擎工厂

### v1.0.0 (2025-11-25)

- ✅ TopHub API 集成
- ✅ 多策略内容提取（69.5% 成功率）
- ✅ Markdown 摘要生成

## 📄 License

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**开发团队**: News2Context Team  
**最后更新**: 2025-11-26
