# News2Context

新闻聚合与上下文提取工具 - 自动从 TopHub Data API 获取新闻源，提取正文内容，生成每日 Markdown 摘要。

## 📋 功能特性

- ✅ 从 TopHub Data API 获取多个新闻源
- ✅ 异步并发请求，提高抓取效率
- ✅ 自动提取文章链接的正文内容
- ✅ 按分类和日期组织新闻
- ✅ 生成格式化的 Markdown 文档
- ✅ 完善的日志记录和错误处理

## 🛠️ 技术栈

- **Python 3.10+**
- **aiohttp**: 异步 HTTP 请求
- **trafilatura**: 网页正文提取
- **loguru**: 日志管理
- **PyYAML**: 配置文件解析

## 📁 项目结构

```
news2context/
├── config/
│   ├── news_sources.yaml      # 新闻源配置
│   ├── .env                    # 环境变量（API Key）
│   └── .env.example            # 环境变量模板
├── src/
│   ├── fetcher.py             # TopHub API 数据获取
│   ├── extractor.py           # 文章内容提取
│   ├── markdown_generator.py  # Markdown 生成
│   └── main.py                # 主程序入口
├── output/                     # 输出目录（按日期组织）
│   └── YYYY-MM-DD/
│       └── news_digest.md
├── logs/                       # 日志文件
├── requirements.txt
└── README.md
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并配置 API Key：

```bash
cp config/.env.example config/.env
```

编辑 `config/.env`：

```env
TOPHUB_API_KEY=your_api_key_here
TOPHUB_API_BASE_URL=https://api.tophubdata.com
OUTPUT_DIR=output
LOG_DIR=logs
MAX_CONCURRENT_REQUESTS=5
REQUEST_TIMEOUT=30
MAX_RETRIES=3
```

### 3. 配置新闻源

编辑 `config/news_sources.yaml`，添加或修改新闻源：

```yaml
categories:
  - name: "财经金融"
    priority: 5
    sources:
      - name: "华尔街见闻-日排行"
        hashid: "G2me3ndwjq"
        url: "https://wallstreetcn.com"
```

### 4. 运行程序

```bash
python src/main.py
```

程序将自动：
1. 从 TopHub API 获取所有配置的新闻源
2. 提取每篇文章的正文内容
3. 生成按日期和分类组织的 Markdown 文件
4. 输出到 `output/YYYY-MM-DD/news_digest.md`

## 📊 输出示例

生成的 Markdown 文件包含：

- 📑 目录（按分类）
- 📰 各分类下的新闻源
- 📝 每篇文章的标题、作者、时间、摘要和正文
- 🔗 原文链接

## 🔧 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `TOPHUB_API_KEY` | TopHub API 密钥 | 必填 |
| `TOPHUB_API_BASE_URL` | API 基础 URL | `https://api.tophubdata.com` |
| `OUTPUT_DIR` | 输出目录 | `output` |
| `LOG_DIR` | 日志目录 | `logs` |
| `MAX_CONCURRENT_REQUESTS` | 最大并发请求数 | `5` |
| `REQUEST_TIMEOUT` | 请求超时时间（秒） | `30` |
| `MAX_RETRIES` | 最大重试次数 | `3` |

### 新闻源配置

在 `config/news_sources.yaml` 中配置新闻源：

```yaml
categories:
  - name: "分类名称"
    priority: 5  # 优先级（1-5）
    sources:
      - name: "新闻源名称"
        hashid: "TopHub hashid"
        url: "网站 URL"
```

## 📝 日志

日志文件保存在 `logs/` 目录下，按日期轮转：

- 文件名格式：`news2context_YYYYMMDD.log`
- 保留期限：30 天
- 日志级别：DEBUG

## 🔄 定时任务（待实现）

可以使用 cron 或其他定时任务工具每天自动运行：

```bash
# 每天早上 6:00 运行
0 6 * * * cd /path/to/news2context && python src/main.py
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**生成时间**: 2025-11-25
