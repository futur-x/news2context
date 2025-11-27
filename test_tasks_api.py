import requests
import json
import time

BASE_URL = "http://localhost:8000/api"
TEST_TASK_NAME = "test_api_task"

def test_create_task():
    print(f"\nTesting POST /tasks (Create {TEST_TASK_NAME})...")
    payload = {
        "name": TEST_TASK_NAME,
        "scene": "Testing API creation",
        "sources": [
            {"name": "36Kr", "hashid": "Q1Vd5Ko85R", "category": "Tech"}
        ],
        "cron": "0 10 * * *",
        "date_range": "today",
        "engine_name": "tophub"
    }
    try:
        response = requests.post(f"{BASE_URL}/tasks", json=payload)
        if response.status_code == 200:
            print("✅ Success:", json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print("❌ Failed:", response.status_code, response.text)
    except Exception as e:
        print("❌ Error:", str(e))

def test_update_task():
    print(f"\nTesting PUT /tasks/{TEST_TASK_NAME}...")
    payload = {
        "scene": "Updated scene description",
        "status": {"enabled": False}
    }
    try:
        response = requests.put(f"{BASE_URL}/tasks/{TEST_TASK_NAME}", json=payload)
        if response.status_code == 200:
            print("✅ Success:", json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print("❌ Failed:", response.status_code, response.text)
    except Exception as e:
        print("❌ Error:", str(e))

def test_run_task():
    print(f"\nTesting POST /tasks/{TEST_TASK_NAME}/run...")
    try:
        response = requests.post(f"{BASE_URL}/tasks/{TEST_TASK_NAME}/run")
        if response.status_code == 200:
            print("✅ Success:", json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print("❌ Failed:", response.status_code, response.text)
    except Exception as e:
        print("❌ Error:", str(e))

def test_delete_task():
    print(f"\nTesting DELETE /tasks/{TEST_TASK_NAME}...")
    try:
        response = requests.delete(f"{BASE_URL}/tasks/{TEST_TASK_NAME}")
        if response.status_code == 200:
            print("✅ Success:", json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print("❌ Failed:", response.status_code, response.text)
    except Exception as e:
        print("❌ Error:", str(e))

if __name__ == "__main__":
    # Ensure server is running
    test_create_task()
    time.sleep(1)
    test_update_task()
    time.sleep(1)
    test_run_task()
    time.sleep(1)
    test_delete_task()
