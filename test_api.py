"""
Phase 5 API 测试脚本
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient
from src.api.app import app

# 添加项目根目录到 python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

client = TestClient(app)

def test_health_check():
    """测试健康检查接口"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] in ["healthy", "degraded"]
    assert "components" in data

def test_list_tasks():
    """测试任务列表接口"""
    response = client.get("/api/tasks")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "tasks" in data
    assert isinstance(data["tasks"], list)

def test_query_empty():
    """测试空查询"""
    payload = {
        "query": "test",
        "limit": 5
    }
    response = client.post("/api/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "results" in data
    assert isinstance(data["results"], list)

if __name__ == "__main__":
    # 手动运行测试
    print("Running API tests...")
    try:
        test_health_check()
        print("✓ Health check passed")
        test_list_tasks()
        print("✓ List tasks passed")
        test_query_empty()
        print("✓ Query passed")
        print("\nAll API tests passed!")
    except Exception as e:
        print(f"\n✗ Tests failed: {str(e)}")
        sys.exit(1)
