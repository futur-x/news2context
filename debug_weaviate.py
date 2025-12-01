import weaviate
import json
import os
import yaml

def debug_weaviate():
    client = weaviate.Client("http://localhost:8080")
    
    # 1. List all classes
    schema = client.schema.get()
    classes = schema.get('classes', [])
    print(f"Found {len(classes)} classes:")
    
    for c in classes:
        class_name = c['class']
        # Get count
        result = client.query.aggregate(class_name).with_meta_count().do()
        count = result['data']['Aggregate'][class_name][0]['meta']['count']
        print(f" - {class_name}: {count} objects")
        
    # 2. Check specific task config
    task_name = "你好啊33"
    config_path = f"config/schedules/{task_name}.yaml"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            collection_name = config['weaviate']['collection']
            print(f"\nTask '{task_name}' uses collection: {collection_name}")
            
            # Query sample
            response = client.query.get(collection_name, ["content", "article_titles"]).with_limit(1).do()
            print("Sample query result:")
            print(json.dumps(response, indent=2, ensure_ascii=False))
    else:
        print(f"\nConfig for '{task_name}' not found")

if __name__ == "__main__":
    debug_weaviate()
