import requests
import json

url = "http://localhost:8043/api/tasks"

payload = {
    "name": "debug_task",
    "scene": "debug scene",
    "sources": [
        {
            "name": "Test Source",
            "hashid": "test_id",
            "category": "tech",
            "url": "http://example.com"
        }
    ],
    "date_range": "last_1_days",
    "cron": "0 8 * * *",
    "engine_name": "tophub"
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
