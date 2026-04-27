#!/usr/bin/env python3
import sys
import json
import requests
from datetime import datetime, timezone

# -- Config ---------------------------------------------------------------------
BASE_URL = "http://localhost:8000"
SYNC_URL = f"{BASE_URL}/api/api_dci/reg/sync/search"
LOGIN_URL = f"{BASE_URL}/api/api_dci/login/"
USERNAME = "Admin"
PASSWORD = "admin123"

def login():
    try:
        r = requests.post(LOGIN_URL, json={"username": USERNAME, "password": PASSWORD}, timeout=10)
        if r.status_code == 200:
            return r.json().get("token", "")
        print(f"[ERROR] Login failed ({r.status_code}): {r.text[:120]}")
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
    return None

def test_sync_search(first_name=None, last_name=None):
    token = login()
    if not token: return

    filters = []
    if first_name: filters.append({"firstName": {"$eq": first_name}})
    if last_name:  filters.append({"lastName":  {"$eq": last_name}})

    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    txn_id = f"txn-sync-{int(datetime.now().timestamp())}"

    payload = {
        "signature": "Signature: fake-signature",
        "header": {
            "version": "1.0.0",
            "message_id": f"msg-{txn_id}",
            "message_ts": now,
            "action": "search",
            "sender_id": "test-sender",
            "receiver_id": "openimis",
        },
        "message": {
            "transaction_id": txn_id,
            "search_request": [{
                "reference_id": f"ref-{txn_id}",
                "timestamp": now,
                "search_criteria": {
                    "version": "1.0.0",
                    "reg_type": "ns:org:RegistryType:FR",
                    "query_type": "expression",
                    "query": {
                        "type": "ns:org:QueryType:expression",
                        "value": {"expression": {"query": {"$and": filters}}}
                    },
                    "pagination": {"page_size": 5, "page_number": 1}
                }
            }]
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    print(f"Sending SYNC search request for: {first_name or '*'} {last_name or '*'}")
    try:
        r = requests.post(SYNC_URL, json=payload, headers=headers, timeout=30)
        print(f"HTTP Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print("\n" + "="*58)
            print("  SYNC SEARCH JSON RESPONSE")
            print("="*58)
            print(json.dumps(data, indent=2))
            print("="*58)
            
            sr = data.get("message", {}).get("search_response", [])
            records = sr[0].get("data", {}).get("reg_records", []) if sr else []
            print(f"\nFound {len(records)} records.")
        else:
            print(f"[ERROR] Request failed: {r.text}")
    except Exception as e:
        print(f"[ERROR] Exception: {e}")

if __name__ == "__main__":
    fn = sys.argv[1] if len(sys.argv) > 1 else "Esther"
    ln = sys.argv[2] if len(sys.argv) > 2 else "Moore"
    test_sync_search(fn, ln)
