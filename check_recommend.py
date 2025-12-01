import requests
import json

def check_recommend():
    url = "http://localhost:8043/api/sources/recommend"
    payload = {
        "scene": "金融新闻",
        "max_sources": 10
    }
    try:
        response = requests.post(url, json=payload)
        data = response.json()
        recommended = data.get('recommended_sources', [])
        print(f"Recommended count: {len(recommended)}")
        
        for i, s in enumerate(recommended):
            print(f"{i+1}. {s['name']} (ID: {s.get('hashid')})")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_recommend()
