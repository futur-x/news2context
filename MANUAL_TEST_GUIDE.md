# News2Context v2.0 人工测试指南

本指南旨在帮助您通过手动操作验证 News2Context 的核心功能。请按照以下步骤逐一进行测试。

## 🛠️ 准备工作

确保您已在项目根目录下，并且环境变量已正确设置。

```bash
# 1. 检查环境变量
cat config/.env

# 确保包含以下 Key:
# OPENAI_API_KEY=sk-...
# TOPHUB_API_KEY=...
# WEAVIATE_URL=http://localhost:8080
```

---

## 💻 第一部分：CLI 界面测试

### 1. 验证配置
检查系统是否能正确加载配置。

```bash
python -m src.cli.main config show
```
**预期结果**:
- 终端显示格式化的配置表格。
- 包含 LLM 配置、引擎配置和 Weaviate 配置。
- 无报错信息。

### 2. 采集向导 (核心功能)
测试创建一个新的采集任务。

```bash
python -m src.cli.main collect wizard
```
**操作步骤**:
1.  输入场景描述: `关注人工智能和 LLM 发展的技术人员`
2.  等待场景分析完成（约 3-5 秒）。
3.  查看推荐的新闻源列表。
4.  输入 `y` 确认创建。

**预期结果**:
- 显示 "场景分析完成"。
- 显示推荐的新闻源（如 "机器之心", "36Kr-AI" 等）。
- 提示 "任务已创建: news-ai-llm-tech"（名称可能不同）。
- 自动开始第一次采集，显示进度条。
- 最后显示 "采集完成！共入库 X 条新闻"。

### 3. 任务管理
查看刚才创建的任务。

```bash
# 列出所有任务
python -m src.cli.main task list

# 查看特定任务详情 (替换为实际任务名)
python -m src.cli.main task show news-ai-llm-tech
```
**预期结果**:
- `list`: 显示任务列表表格，包含任务名、场景、状态等。
- `show`: 显示该任务的详细信息，包括新闻源列表、调度配置等。

### 4. 问答交互
测试 AI 是否能基于采集的新闻回答问题。

```bash
python -m src.cli.main chat interactive
```
**操作步骤**:
1.  选择刚才创建的任务（输入序号）。
2.  输入问题: `最近有什么关于 LLM 的大新闻？`
3.  等待回答。
4.  输入 `exit` 退出。

**预期结果**:
- 系统检索 Weaviate 中的相关新闻。
- 返回基于新闻内容的回答。
- 列出参考的新闻标题和链接。

---

## 🌐 第二部分：API 服务测试

### 1. 启动服务
在一个新的终端窗口中启动 API 服务。

```bash
uvicorn src.api.app:app --host 0.0.0.0 --port 8000
```
**预期结果**:
- 显示 `Uvicorn running on http://0.0.0.0:8000`。

### 2. 测试健康检查
打开浏览器访问或使用 curl:

```bash
curl http://localhost:8000/api/health
```
**预期结果**:
```json
{"success":true,"status":"healthy","components":{"api":"running","weaviate":"connected"}}
```

### 3. 测试任务列表
```bash
curl http://localhost:8000/api/tasks
```
**预期结果**:
- 返回包含刚才创建的任务的 JSON 列表。

### 4. 查看 Swagger 文档
浏览器访问: `http://localhost:8000/docs`
**预期结果**:
- 显示交互式 API 文档页面。

---

## ⏰ 第三部分：后台调度测试

### 1. 启动守护进程
```bash
python -m src.cli.main daemon start
```
**预期结果**:
- 显示 "守护进程已启动 (PID: xxxxx)"。

### 2. 查看状态
```bash
python -m src.cli.main daemon status
```
**预期结果**:
- 显示 "守护进程正在运行"。

### 3. 查看日志
```bash
python -m src.cli.main daemon logs
```
**预期结果**:
- 显示守护进程的最新日志输出。

### 4. 停止守护进程
```bash
python -m src.cli.main daemon stop
```
**预期结果**:
- 显示 "守护进程已停止"。
- 再次运行 `status` 应显示 "守护进程未运行"。

---

## ✅ 测试完成
如果您顺利完成了以上所有步骤，说明 News2Context v2.0 的所有核心组件均工作正常！
