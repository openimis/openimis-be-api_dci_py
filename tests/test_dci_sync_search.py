import requests
import json
from datetime import datetime
import time

# Configuration
BASE_URL = "http://localhost:8000"
SYNC_ENDPOINT = "/api/dci/reg/sync/search"
ASYNC_ENDPOINT = "/api/dci/reg/search"
TOKEN = "your_token_here"  # Replace with actual token if required

def test_search(first_name="John", last_name="Doe", use_async=False):
    endpoint = ASYNC_ENDPOINT if use_async else SYNC_ENDPOINT
    url = f"{BASE_URL}{endpoint}"
    
    # Current timestamp in ISO format with Z
    ts = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    transaction_id = f"trans-{int(time.time())}"
    message_id = f"msg-{int(time.time())}"
    
    # DCI Payload
    payload = {
        "signature": "Signature: fake-signature-for-testing",
        "header": {
            "version": "1.0.0",
            "message_id": message_id,
            "message_ts": ts,
            "action": "search",
            "sender_id": "test-sender",
            "receiver_id": "openimis",
            "sender_uri": "http://localhost:8000/callback"
        },
        "message": {
            "transaction_id": transaction_id,
            "search_request": [
                {
                    "reference_id": f"ref-{int(time.time())}",
                    "timestamp": ts,
                    "search_criteria": {
                        "reg_type": "person",
                        "query_type": "async" if use_async else "sync",
                        "query": {
                            "value": {
                                "expression": {
                                    "query": {
                                        "$and": [
                                            {"firstName": {"$eq": first_name}},
                                            {"lastName": {"$eq": last_name}},
                                            {"gender": {"$eq": "Male"}},
                                            {"dob": {"$eq": "1980-01-01"}},
                                            {"phone": {"$eq": "123456789"}},
                                            {"email": {"$eq": "john.doe@example.com"}}
                                        ]
                                    }
                                }
                            }
                        }
                    }
                }
            ]
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        # "Authorization": f"Bearer {TOKEN}" # Uncomment if auth is needed
    }
    
    mode = "ASYNC" if use_async else "SYNC"
    print(f"Sending {mode} search request for: {first_name} {last_name}...")
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code in [200, 202]:
            result = response.json()
            print("Response Received:")
            print(json.dumps(result, indent=2))
            
            if not use_async:
                # Basic validation for sync results
                if 'message' in result and 'search_response' in result['message']:
                    search_res = result['message']['search_response']
                    if search_res and 'registry_data' in search_res[0]:
                        data = search_res[0]['registry_data'].get('data', [])
                        print(f"\nFound {len(data)} results.")
            else:
                print("\nAsync request accepted (HTTP 202).")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    # Test Sync Search
    print("--- Testing Sync Search ---")
    test_search(first_name="John", last_name="Doe", use_async=False)
    
    print("\n--- Testing Async Search ---")
    test_search(first_name="John", last_name="Doe", use_async=True)
