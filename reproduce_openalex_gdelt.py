import os
import json
import time
import requests

# ----------------- CONFIGURATION -----------------
MAILTO = "stephan@example.com"
BASE_URL = "https://api.openalex.org"
DATA_DIR = "openalex_gdelt_full_dataset"
SEARCH_FILTER = "fulltext.search:GDELT"
PER_PAGE = 200

def fetch_all_works():
    print(f"[*] Starting OpenAlex works download: '{SEARCH_FILTER}'")
    works = []
    cursor = "*"
    while cursor:
        params = {"filter": SEARCH_FILTER, "per_page": PER_PAGE, "cursor": cursor, "mailto": MAILTO}
        res = requests.get(f"{BASE_URL}/works", params=params)
        if res.status_code != 200: break
        data = res.json()
        results = data.get("results", [])
        if not results: break
        works.extend(results)
        cursor = data.get("meta", {}).get("next_cursor")
        print(f"    - Downloaded {len(works)} total works...")
        time.sleep(0.1)
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(os.path.join(DATA_DIR, "gdelt_works.json"), "w", encoding="utf-8") as f:
        json.dump(works, f, indent=2, ensure_ascii=False)
    return works

def fetch_related_entities(entity_type, entity_ids):
    if not entity_ids: return
    print(f"[*] Fetching {len(entity_ids)} {entity_type}...")
    output_dir = os.path.join(DATA_DIR, entity_type)
    os.makedirs(output_dir, exist_ok=True)
    ids_list = list(entity_ids)
    for i in range(0, len(ids_list), 50):
        batch = ids_list[i:i+50]
        params = {"filter": f"openalex:{'|'.join(batch)}", "per_page": 50, "mailto": MAILTO}
        res = requests.get(f"{BASE_URL}/{entity_type}", params=params)
        if res.status_code == 200:
            for entity in res.json().get("results", []):
                eid = entity['id'].split('/')[-1]
                with open(os.path.join(output_dir, f"{eid}.json"), "w", encoding="utf-8") as f:
                    json.dump(entity, f, indent=2, ensure_ascii=False)
        time.sleep(0.1)

def main():
    works = fetch_all_works()
    entities = {"authors": set(), "institutions": set(), "sources": set(), "topics": set(), "publishers": set(), "funders": set()}
    for w in works:
        for auth in w.get("authorships", []):
            if auth.get("author", {}).get("id"): entities["authors"].add(auth["author"]["id"])
            for inst in (auth.get("institutions") or []):
                if inst.get("id"): entities["institutions"].add(inst["id"])
        loc = w.get("primary_location") or {}
        source = loc.get("source") or {}
        if source.get("id"):
            entities["sources"].add(source["id"])
            host_id = source.get("host_organization")
            if host_id:
                if "/P" in host_id: entities["publishers"].add(host_id)
                elif "/I" in host_id: entities["institutions"].add(host_id)
        for t in (w.get("topics") or []):
            if t.get("id"): entities["topics"].add(t["id"])
        for g in (w.get("grants") or []):
            if g.get("funder"): entities["funders"].add(g["funder"])
    for etype, eids in entities.items():
        fetch_related_entities(etype, eids)
    print("\n[FINISH] OpenAlex Extraction complete.")

if __name__ == "__main__":
    main()
