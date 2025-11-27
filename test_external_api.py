import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

# Global variable to store generated token
API_TOKEN = None

def test_generate_token():
    global API_TOKEN
    print("\nTesting POST /external/tokens (Generate Token)...")
    try:
        response = requests.post(f"{BASE_URL}/external/tokens")
        if response.status_code == 200:
            data = response.json()
            API_TOKEN = data.get("token")
            print("✅ Success:")
            print(f"  Token: {API_TOKEN}")
            print(f"  Message: {data.get('message')}")
        else:
            print("❌ Failed:", response.status_code, response.text)
    except Exception as e:
        print("❌ Error:", str(e))

def test_list_tokens():
    print("\nTesting GET /external/tokens (List Tokens)...")
    try:
        response = requests.get(f"{BASE_URL}/external/tokens")
        if response.status_code == 200:
            print("✅ Success:", json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print("❌ Failed:", response.status_code, response.text)
    except Exception as e:
        print("❌ Error:", str(e))

def test_query_without_token():
    print("\nTesting POST /external/news-jj2/query (Without Token - Should Fail)...")
    payload = {
        "query": "AI 新闻",
        "limit": 3
    }
    try:
        response = requests.post(f"{BASE_URL}/external/news-jj2/query", json=payload)
        if response.status_code == 401:
            print("✅ Correctly rejected:", response.json())
        else:
            print("❌ Unexpected:", response.status_code, response.text)
    except Exception as e:
        print("❌ Error:", str(e))

def test_query_with_token():
    if not API_TOKEN:
        print("\n❌ Skipping query test - no token available")
        return
        
    print(f"\nTesting POST /external/news-jj2/query (With Token)...")
    payload = {
        "query": "人工智能",
        "limit": 3
    }
    headers = {
        "Authorization": f"Bearer {API_TOKEN}"
    }
    try:
        response = requests.post(f"{BASE_URL}/external/news-jj2/query", json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("✅ Success:")
            print(f"  Task: {data.get('task_name')}")
            print(f"  Query: {data.get('query')}")
            print(f"  Total Results: {data.get('total')}")
            if data.get('results'):
                print(f"  First Result Score: {data['results'][0].get('score')}")
        else:
            print("❌ Failed:", response.status_code, response.text)
    except Exception as e:
        print("❌ Error:", str(e))

if __name__ == "__main__":
    # Ensure server is running
    test_generate_token()
    time.sleep(1)
    test_list_tokens()
    time.sleep(1)
    test_query_without_token()
    time.sleep(1)
    test_query_with_token()
