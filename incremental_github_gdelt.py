import requests
import json
import time
import os
from datetime import datetime

OUTPUT_FILE = "gdelt_github_repos.json"
BASE_URL = "https://api.github.com/search/repositories"

def fetch_partitioned_repos():
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f: data = json.load(f); existing_ids = {r["id"] for r in data}; all_repos = data
    else: existing_ids, all_repos = set(), []
    
    for year in range(2013, datetime.now().year + 1):
        print(f"[*] Searching GDELT repos created in {year}...")
        page = 1
        while True:
            params = {"q": f"GDELT created:{year}-01-01..{year}-12-31", "per_page": 100, "page": page}
            res = requests.get(BASE_URL, params=params)
            if res.status_code == 403:
                time.sleep(10); continue
            if res.status_code != 200: break
            items = res.json().get("items", [])
            if not items: break
            for item in items:
                if item["id"] not in existing_ids:
                    all_repos.append({"id": item["id"], "name": item["name"], "full_name": item["full_name"], "html_url": item["html_url"], "description": item.get("description"), "stars": item.get("stargazers_count"), "forks": item.get("forks_count"), "language": item.get("language"), "topics": item.get("topics", []), "created_at": item.get("created_at"), "updated_at": item.get("updated_at"), "owner": item.get("owner", {}).get("login")})
                    existing_ids.add(item["id"])
            if len(items) < 100: break
            page += 1; time.sleep(2)
            
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_repos, f, indent=2, ensure_ascii=False)
    print(f"\n[FINISH] GitHub Incremental complete. Total: {len(all_repos)}")

if __name__ == "__main__":
    fetch_partitioned_repos()
