import requests
import json
import sys

def pull_model(model_name="qwen2.5:0.5b"):
    url = "http://host.docker.internal:11434/api/pull"
    payload = {"name": model_name}
    
    print(f"Pulling model: {model_name}...")
    try:
        with requests.post(url, json=payload, stream=True) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if line:
                    data = json.loads(line)
                    status = data.get("status")
                    completed = data.get("completed")
                    total = data.get("total")
                    if completed and total:
                        percent = (completed / total) * 100
                        sys.stdout.write(f"\r{status}: {percent:.1f}%")
                        sys.stdout.flush()
                    else:
                        print(f"{status}")
                        
        print(f"\nSuccessfully pulled {model_name}")
        
    except Exception as e:
        print(f"\nError pulling model: {e}")

if __name__ == "__main__":
    pull_model()
