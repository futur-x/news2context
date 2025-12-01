import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_get_system_settings():
    print("\nTesting GET /settings/system...")
    try:
        response = requests.get(f"{BASE_URL}/settings/system")
        if response.status_code == 200:
            print("✅ Success:", json.dumps(response.json(), indent=2))
        else:
            print("❌ Failed:", response.status_code, response.text)
    except Exception as e:
        print("❌ Error:", str(e))

def test_get_tophub_settings():
    print("\nTesting GET /settings/engines/tophub...")
    try:
        response = requests.get(f"{BASE_URL}/settings/engines/tophub")
        if response.status_code == 200:
            print("✅ Success:", json.dumps(response.json(), indent=2))
        else:
            print("❌ Failed:", response.status_code, response.text)
    except Exception as e:
        print("❌ Error:", str(e))

if __name__ == "__main__":
    # Ensure server is running before testing
    test_get_system_settings()
    test_get_tophub_settings()
