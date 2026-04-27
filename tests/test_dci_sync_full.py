#!/usr/bin/env python3
"""
DCI Sync Search Full Test
=========================
Tests POST /api/api_dci/reg/sync/search against the SPDCI spec:
  https://spdci.github.io/api-standards/release/html/fr_api_v1.0.0.html

The sync endpoint should:
 - Accept the full SPDCI request payload (signature + header + message)
 - Return HTTP 200 with full search results inline (not 202 ACK)
 - Response contains: signature, header (action=on-search, status=succ), message
   with search_response[].data.reg_records

No signature validation for now (signature field is accepted but not verified).
"""

import requests
import json
import time
from datetime import datetime, timezone

BASE_URL = "http://localhost:8000"
LOGIN_URL  = f"{BASE_URL}/api/api_dci/login/"
SYNC_URL   = f"{BASE_URL}/api/api_dci/reg/sync/search"

# - helpers --------------------------------

def get_token(username="Admin", password="admin123"):
    resp = requests.post(LOGIN_URL, json={"username": username, "password": password}, timeout=10)
    if resp.status_code == 200:
        token = resp.json().get("token")
        print(f"[AUTH] [OK] Got token for '{username}'")
        return token
    print(f"[AUTH] [FAIL] Login failed {resp.status_code}: {resp.text}")
    return None

def ts_now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

def make_base_payload(transaction_id, search_criteria_query, ref_id=None, page_size=10, page_number=1):
    """Build a full SPDCI-compliant request payload (no real signature)."""
    ts = ts_now()
    ref_id = ref_id or f"ref-{int(time.time())}"
    return {
        # Signature field - skipped verification per requirement
        "signature": "Signature: namespace=\"spdci\", kidId=\"test-sender|key1|ed25519\", algorithm=\"ed25519\", created=\"1606970629\", expires=\"9999999999\", headers=\"(created) (expires) digest\", signature=\"SKIP_FOR_NOW\"",
        "header": {
            "version": "1.0.0",
            "message_id": f"msg-{int(time.time())}",
            "message_ts": ts,
            "action": "search",
            "sender_id": "spmis.example.org",
            # sender_uri is the callback URL used in async - kept here as per spec
            "sender_uri": "http://localhost:8000/api/api_dci/registry/on-search",
            "receiver_id": "openimis",
            "total_count": 0,
            "is_msg_encrypted": False,
            "meta": {}
        },
        "message": {
            "transaction_id": transaction_id,
            "search_request": [
                {
                    "reference_id": ref_id,
                    "timestamp": ts,
                    "search_criteria": {
                        "version": "1.0.0",
                        "reg_type": "ns:org:RegistryType:Social",
                        "reg_record_type": "Group",
                        "query_type": "expression",
                        "query": {
                            "type": "ns:org:QueryType:expression",
                            "value": {
                                "expression": {
                                    "query": search_criteria_query
                                }
                            }
                        },
                        "sort": [],
                        "pagination": {
                            "page_size": page_size,
                            "page_number": page_number
                        },
                        "consent": {
                            "@context": "https://schema.spdci.org/common/v1/api-schemas/Consent.jsonld",
                            "@type": "Consent",
                            "ts": ts,
                            "purpose": {
                                "text": "Registry search for welfare",
                                "code": "welfare",
                                "ref_uri": "https://spdci.org/consent/welfare"
                            }
                        },
                        "authorize": {
                            "@context": "https://schema.spdci.org/common/v1/api-schemas/Authorize.jsonld",
                            "@type": "Authorize",
                            "ts": ts,
                            "purpose": {
                                "text": "Authorized search",
                                "code": "authorized",
                                "ref_uri": "https://spdci.org/authorize/authorized"
                            }
                        }
                    },
                    "locale": "eng"
                }
            ]
        }
    }


def check_response_structure(resp_json, test_name):
    """Validate the SPDCI-compliant response structure."""
    issues = []
    # Top-level keys
    for key in ["header", "message"]:
        if key not in resp_json:
            issues.append(f"Missing top-level key: '{key}'")

    header = resp_json.get("header", {})
    # header fields per spec
    for field in ["version", "message_id", "message_ts", "action", "sender_id", "receiver_id", "status"]:
        if field not in header:
            issues.append(f"Missing header field: '{field}'")

    if header.get("action") != "on-search":
        issues.append(f"header.action should be 'on-search', got '{header.get('action')}'")
    if header.get("status") != "succ":
        issues.append(f"header.status should be 'succ', got '{header.get('status')}'")

    message = resp_json.get("message", {})
    if "transaction_id" not in message:
        issues.append("Missing message.transaction_id")
    if "search_response" not in message:
        issues.append("Missing message.search_response")
    else:
        sr = message["search_response"]
        if not isinstance(sr, list):
            issues.append("message.search_response should be a list")
        elif len(sr) > 0:
            item = sr[0]
            for f in ["reference_id", "timestamp", "status", "data", "pagination"]:
                if f not in item:
                    issues.append(f"search_response[0] missing field: '{f}'")
            data = item.get("data", {})
            for f in ["version", "reg_type", "reg_record_type", "reg_records"]:
                if f not in data:
                    issues.append(f"search_response[0].data missing field: '{f}'")

    if issues:
        print(f"\n  [WARN] Structure issues in '{test_name}':")
        for i in issues:
            print(f"     * {i}")
    else:
        print(f"  [OK] Response structure is SPDCI-compliant")

    return len(issues) == 0


def run_test(test_name, query, token, page_size=10):
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print('='*60)

    transaction_id = f"txn-sync-{int(time.time())}"
    payload = make_base_payload(transaction_id, query, page_size=page_size)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    print(f"  -> POST {SYNC_URL}")
    print(f"  -> transaction_id: {transaction_id}")
    print(f"  -> query: {json.dumps(query)}")

    try:
        resp = requests.post(SYNC_URL, json=payload, headers=headers, timeout=30)
    except requests.exceptions.ConnectionError as e:
        print(f"  [FAIL] Connection error: {e}")
        return

    print(f"\n  HTTP Status: {resp.status_code}", end="")

    if resp.status_code == 200:
        print(" [OK] (expected 200 for sync)")
    elif resp.status_code == 400:
        print(" [FAIL] Bad Request")
        print(f"  Body: {resp.text[:500]}")
        return
    elif resp.status_code == 403:
        print(" [FAIL] Forbidden - check permissions")
        print(f"  Body: {resp.text[:300]}")
        return
    else:
        print(f" [WARN] Unexpected")
        print(f"  Body: {resp.text[:500]}")
        return

    try:
        data = resp.json()
    except Exception:
        print(f"  [FAIL] Non-JSON response: {resp.text[:200]}")
        return

    # Structural validation
    is_valid = check_response_structure(data, test_name)

    # Show results summary
    message = data.get("message", {})
    sr = message.get("search_response", [])
    rec_count = 0
    if sr:
        records = sr[0].get("data", {}).get("reg_records", [])
        rec_count = len(records)
        print(f"\n  REC Records returned: {rec_count}")

        if rec_count > 0:
            print(f"\n  Sample record structure (first record keys):")
            print(f"     {list(records[0].keys()) if isinstance(records[0], dict) else type(records[0])}")
    else:
        print(f"\n  REC No search_response items")

    pagination = sr[0].get("pagination", {}) if sr else {}
    print(f"  PAGE Pagination: {pagination}")
    print(f"  AUTH Header status: {data.get('header', {}).get('status')}")
    print(f"  AUTH Header action: {data.get('header', {}).get('action')}")

    # Full response dump
    print(f"\n  Full response (pretty):")
    print(json.dumps(data, indent=4, default=str))


# --------------------------------------
# MAIN
# --------------------------------------

if __name__ == "__main__":
    print("\n" + "="*60)
    print("DCI SYNC SEARCH - FULL SPDCI PATTERN TEST")
    print("="*60)

    token = get_token()
    if not token:
        print("Cannot proceed without token. Exiting.")
        exit(1)

    # - Test 1: Search by first name -------------------
    run_test(
        "T1: Search by firstName only",
        query={"$and": [{"firstName": {"$eq": "John"}}]},
        token=token
    )

    # - Test 2: Search by last name -------------------
    run_test(
        "T2: Search by lastName only",
        query={"$and": [{"lastName": {"$eq": "Doe"}}]},
        token=token
    )

    # - Test 3: firstName + lastName (AND) ---------------
    run_test(
        "T3: Search firstName + lastName combined",
        query={"$and": [
            {"firstName": {"$eq": "John"}},
            {"lastName":  {"$eq": "Doe"}}
        ]},
        token=token
    )

    # - Test 4: firstName + gender --------------------
    run_test(
        "T4: Search firstName + gender",
        query={"$and": [
            {"firstName": {"$eq": "John"}},
            {"gender": {"$eq": "Male"}}
        ]},
        token=token
    )

    # - Test 5: Empty query (return all, paginated) -----------
    run_test(
        "T5: Empty $and filters (all records, page_size=5)",
        query={"$and": []},
        token=token,
        page_size=5
    )

    # - Test 6: Non-existent person -------------------
    run_test(
        "T6: Search for non-existent person",
        query={"$and": [{"firstName": {"$eq": "ZZZNOBODYZZZXXX"}}]},
        token=token
    )

    # - Test 7: Full spec payload including all optional fields -----
    print(f"\n{'='*60}")
    print("TEST: T7: Verify response contains required SPDCI fields")
    print('='*60)
    ts = ts_now()
    txn_id = f"txn-full-spec-{int(time.time())}"
    payload = {
        "signature": "Signature: namespace=\"spdci\", kidId=\"spmis.example.org|key1|ed25519\", algorithm=\"ed25519\", created=\"1606970629\", expires=\"9999999999\", headers=\"(created) (expires) digest\", signature=\"SKIP\"",
        "header": {
            "version": "1.0.0",
            "message_id": "msg-full-spec-001",
            "message_ts": ts,
            "action": "search",
            "sender_id": "spmis.example.org",
            "sender_uri": "http://spmis.example.org/consumer-namespace/callback/on-search",
            "receiver_id": "openimis.example.org",
            "total_count": 0,
            "is_msg_encrypted": False,
            "meta": {}
        },
        "message": {
            "transaction_id": txn_id,
            "search_request": [{
                "reference_id": "SDFRTYUX-001",
                "timestamp": ts,
                "search_criteria": {
                    "version": "1.0.0",
                    "reg_type": "ns:org:RegistryType:Social",
                    "reg_record_type": "Group",
                    "query_type": "expression",
                    "query": {
                        "type": "ns:org:QueryType:expression",
                        "value": {
                            "expression": {
                                "query": {
                                    "$and": [{"firstName": {"$eq": "John"}}]
                                }
                            }
                        }
                    },
                    "sort": [{"attribute_name": "firstName", "sort_order": "asc"}],
                    "pagination": {"page_size": 10, "page_number": 1},
                    "consent": {
                        "@context": "https://schema.spdci.org/common/v1/api-schemas/Consent.jsonld",
                        "@type": "Consent",
                        "ts": ts,
                        "purpose": {
                            "text": "Registry search",
                            "code": "welfare",
                            "ref_uri": "https://spdci.org/consent"
                        }
                    },
                    "authorize": {
                        "@context": "https://schema.spdci.org/common/v1/api-schemas/Authorize.jsonld",
                        "@type": "Authorize",
                        "ts": ts,
                        "purpose": {
                            "text": "Authorized",
                            "code": "authorized",
                            "ref_uri": "https://spdci.org/authorize"
                        }
                    }
                },
                "locale": "eng"
            }]
        }
    }
    resp = requests.post(SYNC_URL, json=payload, headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"}, timeout=30)
    print(f"  HTTP Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        ok = check_response_structure(data, "T7")
        print(f"\n  Full Response:")
        print(json.dumps(data, indent=4, default=str))
    else:
        print(f"  Response: {resp.text[:500]}")

    print(f"\n{'='*60}")
    print("ALL SYNC SEARCH TESTS DONE")
    print('='*60)
