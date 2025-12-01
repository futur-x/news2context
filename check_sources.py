import requests
from collections import Counter

def check_sources():
    url = "http://localhost:8043/api/sources"
    try:
        response = requests.get(url)
        sources = response.json()
        print(f"Total sources: {len(sources)}")
        
        ids = [s.get('hashid') or s.get('id') for s in sources]
        names = [s.get('name') for s in sources]
        
        id_counts = Counter(ids)
        name_counts = Counter(names)
        
        dup_ids = {k: v for k, v in id_counts.items() if v > 1}
        dup_names = {k: v for k, v in name_counts.items() if v > 1}
        
        print(f"Duplicate IDs: {len(dup_ids)}")
        if dup_ids:
            print(f"Sample duplicate IDs: {list(dup_ids.items())[:5]}")
            
        print(f"Duplicate Names: {len(dup_names)}")
        if dup_names:
            print(f"Sample duplicate Names: {list(dup_names.items())[:5]}")
            
        # Check Hibor specifically
        hibor = [s for s in sources if "慧博" in s.get('name', '')]
        print(f"Hibor sources count: {len(hibor)}")
        for h in hibor:
            print(f" - {h['name']} (ID: {h.get('hashid') or h.get('id')})")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_sources()
