#!/bin/bash

# News2Context Docker 部署脚本
set -e

echo "=========================================="
echo "  News2Context Docker 部署工具"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker 未安装${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}错误: docker-compose 未安装${NC}"
    exit 1
fi

# 检查配置文件
if [ ! -f "config/.env" ]; then
    echo -e "${YELLOW}警告: config/.env 不存在${NC}"
    if [ -f "config/.env.example" ]; then
        echo "正在从 config/.env.example 创建配置文件..."
        cp config/.env.example config/.env
        echo -e "${YELLOW}请编辑 config/.env 并填入必要的 API Keys${NC}"
        read -p "按回车继续..."
    else
        echo -e "${RED}错误: 找不到 config/.env.example${NC}"
        exit 1
    fi
fi

# 显示菜单
show_menu() {
    echo ""
    echo "请选择操作："
    echo "  1) 启动所有服务"
    echo "  2) 停止所有服务"
    echo "  3) 重启所有服务"
    echo "  4) 查看服务状态"
    echo "  5) 查看日志"
    echo "  6) 重新构建并启动"
    echo "  7) 清理所有数据（危险）"
    echo "  0) 退出"
    echo ""
}

# 启动服务
start_services() {
    echo -e "${GREEN}正在启动服务...${NC}"
    docker-compose up -d
    echo ""
    echo -e "${GREEN}✓ 服务已启动！${NC}"
    echo ""
    echo "访问地址："
    echo "  前端: http://localhost:8042"
    echo "  后端: http://localhost:8043"
    echo "  API 文档: http://localhost:8043/docs"
    echo ""
}

# 停止服务
stop_services() {
    echo -e "${YELLOW}正在停止服务...${NC}"
    docker-compose down
    echo -e "${GREEN}✓ 服务已停止${NC}"
}

# 重启服务
restart_services() {
    echo -e "${YELLOW}正在重启服务...${NC}"
    docker-compose restart
    echo -e "${GREEN}✓ 服务已重启${NC}"
}

# 查看状态
show_status() {
    echo -e "${GREEN}服务状态：${NC}"
    docker-compose ps
}

# 查看日志
show_logs() {
    echo "选择要查看的服务日志："
    echo "  1) 所有服务"
    echo "  2) 前端"
    echo "  3) 后端"
    echo "  4) 守护进程"
    echo "  5) Weaviate"
    read -p "请选择 (1-5): " log_choice

    case $log_choice in
        1) docker-compose logs -f ;;
        2) docker-compose logs -f frontend ;;
        3) docker-compose logs -f backend ;;
        4) docker-compose logs -f scheduler ;;
        5) docker-compose logs -f weaviate ;;
        *) echo "无效选择" ;;
    esac
}

# 重新构建
rebuild_services() {
    echo -e "${YELLOW}正在重新构建并启动服务...${NC}"
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d
    echo -e "${GREEN}✓ 重新构建完成${NC}"
}

# 清理数据
clean_all() {
    echo -e "${RED}警告: 这将删除所有容器、数据卷和数据！${NC}"
    read -p "确定要继续吗？(yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        docker-compose down -v
        echo -e "${GREEN}✓ 已清理所有数据${NC}"
    else
        echo "已取消"
    fi
}

# 主循环
while true; do
    show_menu
    read -p "请选择 (0-7): " choice

    case $choice in
        1) start_services ;;
        2) stop_services ;;
        3) restart_services ;;
        4) show_status ;;
        5) show_logs ;;
        6) rebuild_services ;;
        7) clean_all ;;
        0) echo "再见！"; exit 0 ;;
        *) echo -e "${RED}无效选择，请重试${NC}" ;;
    esac

    read -p "按回车继续..."
done
