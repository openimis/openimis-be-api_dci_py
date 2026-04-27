#!/usr/bin/env python3
"""
DCI Sync Search - Quick Interactive Tester
==========================================
Run this directly to verify your DCI sync search endpoint is working.

Usage:
    python3 test_dci_quick.py
    python3 test_dci_quick.py Ana
    python3 test_dci_quick.py Ana Ali
"""

import sys
import json
import time
import requests
from datetime import datetime, timezone

# -- Config -------------------------------------------------------------------
BASE_URL   = "http://localhost:8000"
LOGIN_URL  = f"{BASE_URL}/api/api_dci/login/"
SYNC_URL   = f"{BASE_URL}/api/api_dci/reg/sync/search"
USERNAME   = "Admin"
PASSWORD   = "admin123"
# -----------------------------------------------------------------------------

# Output prefixes
def ok(msg):   print(f"  [OK] {msg}")
def err(msg):  print(f"  [ERROR] {msg}")
def info(msg): print(f"  [INFO] {msg}")
def warn(msg): print(f"  [WARN] {msg}")


def login():
    try:
        r = requests.post(LOGIN_URL, json={"username": USERNAME, "password": PASSWORD}, timeout=10)
        if r.status_code == 200:
            token = r.json().get("token", "")
            ok(f"Logged in as '{USERNAME}'")
            return token
        err(f"Login failed ({r.status_code}): {r.text[:100]}")
    except requests.exceptions.ConnectionError:
        err(f"Cannot connect to {BASE_URL} - is the server running?")
    return None


def sync_search(first_name=None, last_name=None, page_size=10, token=None):
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    txn_id  = f"txn-{int(time.time())}"
    ref_id  = f"ref-{int(time.time())}"

    # Build $and filter list
    and_filters = []
    if first_name:
        and_filters.append({"firstName": {"$eq": first_name}})
    if last_name:
        and_filters.append({"lastName": {"$eq": last_name}})

    payload = {
        "signature": (
            'Signature: namespace="spdci", kidId="spmis.example.org|key1|ed25519",'
            ' algorithm="ed25519", created="1606970629", expires="9999999999",'
            ' headers="(created) (expires) digest", signature="NO_SIG_CHECK"'
        ),
        "header": {
            "version": "1.0.0",
            "message_id": f"msg-{txn_id}",
            "message_ts": ts,
            "action": "search",
            "sender_id": "spmis.example.org",
            "sender_uri": "http://spmis.example.org/callback/on-search",
            "receiver_id": "openimis",
            "total_count": 0,
            "is_msg_encrypted": False,
            "meta": {}
        },
        "message": {
            "transaction_id": txn_id,
            "search_request": [{
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
                                "query": {"$and": and_filters}
                            }
                        }
                    },
                    "sort": [],
                    "pagination": {"page_size": page_size, "page_number": 1},
                    "consent": {
                        "@context": "https://schema.spdci.org/common/v1/api-schemas/Consent.jsonld",
                        "@type": "Consent",
                        "ts": ts,
                        "purpose": {"text": "Registry search", "code": "welfare",
                                    "ref_uri": "https://spdci.org/consent"}
                    },
                    "authorize": {
                        "@context": "https://schema.spdci.org/common/v1/api-schemas/Authorize.jsonld",
                        "@type": "Authorize",
                        "ts": ts,
                        "purpose": {"text": "Authorized", "code": "authorized",
                                    "ref_uri": "https://spdci.org/authorize"}
                    }
                },
                "locale": "eng"
            }]
        }
    }

    hdrs = {"Content-Type": "application/json"}
    if token:
        hdrs["Authorization"] = f"Bearer {token}"

    try:
        r = requests.post(SYNC_URL, json=payload, headers=hdrs, timeout=30)
    except requests.exceptions.ConnectionError as e:
        err(f"Connection error: {e}")
        return None

    return r


def display_results(resp):
    """Pretty-print the SPDCI response."""
    print()
    print(f"  -- Response {'-'*38}")
    print(f"  HTTP Status  : {resp.status_code}")

    if resp.status_code != 200:
        err(f"Non-200 response: {resp.text[:300]}")
        return

    try:
        data = resp.json()
    except Exception:
        err("Response is not valid JSON")
        print(f"  Raw: {resp.text[:300]}")
        return

    header  = data.get("header", {})
    message = data.get("message", {})

    # Header check
    action = header.get("action", "?")
    status = header.get("status", "?")
    txn_id = message.get("transaction_id", "?")

    print(f"  action       : {action}  ", end="")
    print(f"{'[OK]' if action == 'on-search' else '[ERR] (expected on-search)'}")
    print(f"  status       : {status}  ", end="")
    print(f"{'[OK]' if status == 'succ' else '[ERR] (expected succ)'}")
    print(f"  transaction  : {txn_id}")

    # Records
    sr = message.get("search_response", [])
    if not sr:
        warn("search_response list is empty")
        return

    item       = sr[0]
    rec_status = item.get("status")
    pagination = item.get("pagination", {})
    records    = item.get("data", {}).get("reg_records", [])
    reg_type   = item.get("data", {}).get("reg_type", "?")

    print(f"  reg_type     : {reg_type}")
    print(f"  page_size    : {pagination.get('page_size')}  "
          f"page_number: {pagination.get('page_number')}  "
          f"total: {pagination.get('total_count')}")
    print(f"  records found: {len(records)}")

    if records:
        print()
        print(f"  -- Records {'-'*39}")
        for i, rec in enumerate(records, 1):
            head_info   = rec.get("group_head_info", {})
            demo        = head_info.get("demographic_info", {})
            name        = demo.get("name", {})
            given       = name.get("given_name", "-")
            surname     = name.get("surname",  "-")
            sex         = demo.get("sex", "-")
            birth       = demo.get("birth_date", "-")[:10] if demo.get("birth_date") else "-"
            group_type  = rec.get("group_type", "-")
            group_size  = rec.get("group_size", "-")
            reg_date    = rec.get("registration_date", "-")[:10] if rec.get("registration_date") else "-"

            identifiers = rec.get("group_identifier", [])
            id_str = ", ".join(f"{x['identifier_type']}:{x['identifier_value']}"
                               for x in identifiers) if identifiers else "-"

            print(f"  [{i}] {given} {surname}  "
                  f"| sex={sex} | dob={birth} | group={group_type} "
                  f"| size={group_size} | reg={reg_date}")
            print(f"       ID: {id_str or '-'}")
    else:
        info("No records matched the search criteria")


def check_structure(data):
    """Run spec compliance checks on the response."""
    checks = [
        ("Top-level 'header' present",  "header" in data),
        ("Top-level 'message' present", "message" in data),
        ("header.action = 'on-search'", data.get("header", {}).get("action") == "on-search"),
        ("header.status = 'succ'",      data.get("header", {}).get("status") == "succ"),
        ("message.transaction_id set",  bool(data.get("message", {}).get("transaction_id"))),
        ("message.search_response list",isinstance(data.get("message", {}).get("search_response"), list)),
    ]
    sr = data.get("message", {}).get("search_response", [])
    if sr:
        item = sr[0]
        checks += [
            ("search_response[0].reference_id", "reference_id" in item),
            ("search_response[0].status",        "status"      in item),
            ("search_response[0].timestamp",     "timestamp"   in item),
            ("search_response[0].data",          "data"        in item),
            ("search_response[0].pagination",    "pagination"  in item),
            ("data.reg_type",        "reg_type"        in item.get("data", {})),
            ("data.reg_record_type", "reg_record_type" in item.get("data", {})),
            ("data.reg_records",     "reg_records"     in item.get("data", {})),
        ]

    print()
    print(f"  -- SPDCI Compliance Checks {'-'*25}")
    all_pass = True
    for label, passed in checks:
        if passed:
            print(f"  [OK] {label}")
        else:
            print(f"  [FAIL] {label}")
            all_pass = False

    print()
    if all_pass:
        ok("All SPDCI spec checks passed!")
    else:
        err("Some checks failed - see above")
    return all_pass


# -- MAIN ----------------------------------------------------------------------
if __name__ == "__main__":
    args = sys.argv[1:]
    first_name = args[0] if len(args) >= 1 else None
    last_name  = args[1] if len(args) >= 2 else None

    print()
    print(f"{'='*54}")
    print(f"  DCI Sync Search - Quick Test")
    print(f"{'='*54}")
    print(f"  Endpoint : {SYNC_URL}")
    if first_name or last_name:
        print(f"  Search   : firstName='{first_name or '*'}' lastName='{last_name or '*'}'")
    else:
        print(f"  Search   : (all records, page_size=5)")
    print()

    # Step 1: Login
    info("Step 1/3 - Authenticating...")
    token = login()
    if not token:
        sys.exit(1)

    # Step 2: Send sync search
    info("Step 2/3 - Sending sync search request...")
    resp = sync_search(
        first_name=first_name,
        last_name=last_name,
        page_size=5 if not first_name and not last_name else 10,
        token=token
    )
    if resp is None:
        sys.exit(1)

    display_results(resp)

    # Step 3: Check SPDCI compliance
    info("Step 3/3 - Checking SPDCI spec compliance...")
    if resp.status_code == 200:
        try:
            check_structure(resp.json())
        except Exception as e:
            err(f"Could not parse JSON: {e}")

    print()
    print(f"{'='*54}")
    print(f"  Done. Try: python3 test_dci_quick.py Ana")
    print(f"             python3 test_dci_quick.py Ana Ali")
    print(f"{'='*54}")
    print()
