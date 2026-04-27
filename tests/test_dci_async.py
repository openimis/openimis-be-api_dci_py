#!/usr/bin/env python3
"""
DCI Async Search - Full End-to-End Test (Farmer Registry)
==========================================================
This script:
  1. Starts a mock subscriber callback server on port 8099
  2. Sends POST /api/api_dci/reg/search  ->  gets HTTP 202 ACK
  3. Waits for openIMIS to push Farmer Registry results to the callback URL
  4. Polls /api/api_dci/reg/txn/status in parallel
  5. Dumps the full raw JSON response
  6. Prints a summary report

Run:
    python3 test_dci_async.py
    python3 test_dci_async.py Ana          # search by first name
    python3 test_dci_async.py Ana Ali      # search by first + last
"""

import sys
import json
import time
import threading
import requests
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler

# -- Config ---------------------------------------------------------------------
BASE_URL      = "http://localhost:8000"
CALLBACK_PORT = 8099
CALLBACK_HOST = "127.0.0.1"
CALLBACK_PATH = "/on-search"
CALLBACK_URL  = f"http://{CALLBACK_HOST}:{CALLBACK_PORT}{CALLBACK_PATH}"

LOGIN_URL     = f"{BASE_URL}/api/api_dci/login/"
ASYNC_URL     = f"{BASE_URL}/api/api_dci/reg/search"
TXN_URL       = f"{BASE_URL}/api/api_dci/reg/txn/status"

USERNAME      = "Admin"
PASSWORD      = "admin123"
TIMEOUT_SEC   = 30   # max seconds to wait for callback push
POLL_INTERVAL = 2    # seconds between txn/status polls
# -----------------------------------------

# Shared state - callback server writes here, main thread reads
_callback_received = threading.Event()
_callback_payload  = {}
_callback_lock     = threading.Lock()

# Output prefixes
def ok(m):   print(f"  [OK] {m}")
def err(m):  print(f"  [ERROR] {m}")
def info(m): print(f"  [INFO] {m}")
def warn(m): print(f"  [WARN] {m}")
def sep():   print(f"  {'-'*56}")


# -- Mock Callback Server -------------------------------------------------------

class CallbackHandler(BaseHTTPRequestHandler):
    """Receives the async push from openIMIS."""

    def do_POST(self):
        length  = int(self.headers.get("Content-Length", 0))
        body    = self.rfile.read(length)
        arrived = datetime.now(timezone.utc).strftime('%H:%M:%S UTC')

        try:
            data = json.loads(body)
        except Exception:
            data = {"_raw": body.decode(errors="replace")}

        with _callback_lock:
            _callback_payload.update(data)
            _callback_payload["_arrived_at"] = arrived
            _callback_payload["_raw_json"]   = body.decode(errors="replace")

        _callback_received.set()

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status": "received"}')

    def log_message(self, fmt, *args):
        pass   # suppress access log noise


def start_callback_server():
    server = HTTPServer((CALLBACK_HOST, CALLBACK_PORT), CallbackHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


# -- Helpers --------------------------------------------------------------------

def login():
    try:
        r = requests.post(LOGIN_URL,
                          json={"username": USERNAME, "password": PASSWORD},
                          timeout=10)
        if r.status_code == 200:
            token = r.json().get("token", "")
            ok(f"Logged in as '{USERNAME}'")
            return token
        err(f"Login failed ({r.status_code}): {r.text[:120]}")
    except requests.exceptions.ConnectionError:
        err(f"Cannot connect to {BASE_URL} - is the server running?")
    return None


def ts():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def make_async_payload(first_name=None, last_name=None):
    txn_id = f"txn-async-{int(time.time())}"
    ref_id = f"ref-async-{int(time.time())}"
    now    = ts()

    filters = []
    if first_name: filters.append({"firstName": {"$eq": first_name}})
    if last_name:  filters.append({"lastName":  {"$eq": last_name}})

    return txn_id, {
        "signature": (
            'Signature: namespace="spdci", kidId="spmis.example.org|key1|ed25519",'
            ' algorithm="ed25519", created="1606970629", expires="9999999999",'
            ' headers="(created) (expires) digest", signature="NO_SIG_CHECK"'
        ),
        "header": {
            "version":          "1.0.0",
            "message_id":       f"msg-{txn_id}",
            "message_ts":       now,
            "action":           "search",
            "sender_id":        "spmis.example.org",
            "sender_uri":       CALLBACK_URL,   # <- openIMIS POSTs results here
            "receiver_id":      "openimis",
            "total_count":      0,
            "is_msg_encrypted": False,
            "meta":             {}
        },
        "message": {
            "transaction_id": txn_id,
            "search_request": [{
                "reference_id": ref_id,
                "timestamp":    now,
                "search_criteria": {
                    "version":         "1.0.0",
                    "reg_type":        "ns:org:RegistryType:FR",          # Farmer Registry
                    "reg_record_type": "spdci-extensions-dci:Farmer",
                    "query_type":      "expression",
                    "query": {
                        "type":  "ns:org:QueryType:expression",
                        "value": {"expression": {"query": {"$and": filters}}}
                    },
                    "sort":       [],
                    "pagination": {"page_size": 5, "page_number": 1},
                    "consent": {
                        "@context": "https://schema.spdci.org/common/v1/api-schemas/Consent.jsonld",
                        "@type":    "Consent",
                        "ts":       now,
                        "purpose":  {"text": "Farmer registry async search",
                                     "code": "welfare",
                                     "ref_uri": "https://spdci.org/consent"}
                    },
                    "authorize": {
                        "@context": "https://schema.spdci.org/common/v1/api-schemas/Authorize.jsonld",
                        "@type":    "Authorize",
                        "ts":       now,
                        "purpose":  {"text": "Authorized",
                                     "code": "authorized",
                                     "ref_uri": "https://spdci.org/authorize"}
                    }
                },
                "locale": "eng"
            }]
        }
    }


def poll_txn_status(txn_id, token, max_polls=5):
    """Poll /reg/txn/status until succ/rjct or max_polls reached."""
    hdrs = {"Content-Type": "application/json",
            "Authorization": f"Bearer {token}"}

    for attempt in range(1, max_polls + 1):
        time.sleep(POLL_INTERVAL)
        payload = {
            "header": {
                "version":          "1.0.0",
                "message_id":       f"poll-{attempt}",
                "message_ts":       ts(),
                "action":           "txn-status",
                "sender_id":        "spmis.example.org",
                "receiver_id":      "openimis",
                "is_msg_encrypted": False
            },
            "message": {
                "transaction_id": txn_id,
                "txnstatus_request": {
                    "txn_type":       "search",
                    "attribute_type": "transaction_id",
                    "attribute_value": txn_id
                }
            }
        }
        try:
            r = requests.post(TXN_URL, json=payload, headers=hdrs, timeout=10)
            data = r.json()
            status_val = data.get("header", {}).get("status", "?")
            print(f"    Poll #{attempt}: status = {status_val}")
            if status_val in ("succ", "rjct"):
                return data
        except Exception as e:
            warn(f"Poll #{attempt} failed: {e}")
    return None


# -- Farmer record display ------------------------------------------------------

def show_farmer_records(records, title="Farmer Records"):
    """Pretty-print FRPerson / Farmer records."""
    if not records:
        info("No matching farmer records found")
        return

    print(f"\n  -- {title} ({len(records)} returned) {'-'*18}")
    for i, rec in enumerate(records, 1):
        rtype = rec.get("@type", "?")

        # famer_personal_details block
        personal  = rec.get("famer_personal_details", {})
        demo      = personal.get("demographic_info", {})
        name      = demo.get("name", {})
        first     = name.get("first_name", "-")
        last      = name.get("last_name",  "-")
        gender    = demo.get("gender", "-")
        dob       = (demo.get("date_of_birth") or "-")[:10]
        phone     = demo.get("phone", "-")
        email     = demo.get("email", "-")
        edu       = demo.get("education_level", "-")
        m_id      = personal.get("member_identifier", {})
        farmer_id = m_id.get("identifier_value", "-") if isinstance(m_id, dict) else "-"

        # farm_details
        farms     = rec.get("farm_details", [])
        farm_summary = []
        for f in farms:
            size  = f.get("land_size", "?")
            unit  = f.get("land_unit", "?")
            crop  = f.get("primary_crop", "?")
            irrig = f.get("irrigation_type", "?")
            farm_summary.append(f"{size}{unit} {crop} ({irrig})")

        # family_details
        family    = rec.get("family_details", {})
        hh_size   = family.get("household_size", "-")
        marital   = family.get("marital_status", "-")

        # machineries
        mach      = rec.get("machineries_details", [])
        mach_str  = ", ".join(m.get("machinery_type","?") for m in mach) or "none"

        reg_date  = (rec.get("registration_date") or "-")[:10]

        print(f"\n  [{i}] {first} {last}  |  @type: {rtype}")
        print(f"       FarmerID  : {farmer_id}")
        print(f"       gender    : {gender}  |  dob: {dob}  |  edu: {edu}")
        print(f"       phone     : {phone}  |  email: {email}")
        print(f"       household : size={hh_size}  |  marital={marital}")
        print(f"       farms     : {' | '.join(farm_summary) if farm_summary else 'none'}")
        print(f"       machinery : {mach_str}")
        print(f"       registered: {reg_date}")


def dump_json(data, title="Full JSON Response"):
    """Print the complete raw JSON with colour header."""
    # Remove internal tracking keys before printing
    clean = {k: v for k, v in data.items() if not k.startswith("_")}
    print(f"\n  {'-'*56}")
    print(f"  {title}")
    print(f"  {'-'*56}")
    print(json.dumps(clean, indent=2, default=str))
    print(f"  {'-'*56}")


def verify_callback_payload(data):
    """Check the callback payload against SPDCI spec."""
    checks = [
        ("'header' present",              "header"  in data),
        ("'message' present",             "message" in data),
        ("header.action = 'on-search'",   data.get("header", {}).get("action") == "on-search"),
        ("header.status = 'succ'",        data.get("header", {}).get("status") == "succ"),
        ("message.transaction_id set",    bool(data.get("message", {}).get("transaction_id"))),
        ("search_response is a list",     isinstance(
            data.get("message", {}).get("search_response"), list)),
    ]
    sr = data.get("message", {}).get("search_response", [])
    if sr:
        item = sr[0]
        checks += [
            ("search_response[0].data",      "data"       in item),
            ("data.reg_records is a list",   isinstance(item.get("data", {}).get("reg_records"), list)),
            ("search_response[0].pagination","pagination" in item),
            ("search_response[0].status",    item.get("status") == "succ"),
            ("reg_type = FR",                item.get("data", {}).get("reg_type") == "ns:org:RegistryType:FR"),
            ("reg_record_type = Farmer",     "Farmer" in item.get("data", {}).get("reg_record_type", "")),
        ]
    print(f"\n  -- SPDCI Compliance Checks {'-'*27}")
    all_ok = True
    for label, passed in checks:
        if passed: print(f"  [OK] {label}")
        else:      print(f"  [FAIL] {label}"); all_ok = False
    return all_ok


# -- MAIN -----------------------------------------------------------------------

def main():
    args       = sys.argv[1:]
    first_name = args[0] if len(args) >= 1 else None
    last_name  = args[1] if len(args) >= 2 else None

    print()
    print("="*58)
    print("  DCI Async Search - Farmer Registry End-to-End Test")
    print("="*58)
    print(f"  Async endpoint  : {ASYNC_URL}")
    print(f"  Callback server : {CALLBACK_URL}")
    print(f"  Registry type   : Farmer (ns:org:RegistryType:FR)")
    if first_name or last_name:
        print(f"  Search          : firstName='{first_name or '*'}'  lastName='{last_name or '*'}'")
    else:
        print(f"  Search          : (all farmer records, page_size=5)")
    print()

    # -- Step 1: Start callback server -----------------------------------------
    info("Step 1/5 - Starting mock subscriber callback server (port 8099)...")
    try:
        server = start_callback_server()
        ok(f"Callback server ready at {CALLBACK_URL}")
    except OSError as e:
        err(f"Cannot start callback server: {e}")
        err("Port 8099 already in use - kill the old process and retry.")
        sys.exit(1)
    sep()

    # -- Step 2: Login ---------------------------------------------------------
    info("Step 2/5 - Authenticating with openIMIS...")
    token = login()
    if not token:
        sys.exit(1)
    sep()

    # -- Step 3: Send async search ---------------------------------------------
    info("Step 3/5 - Sending async search request (expecting HTTP 202 ACK)...")
    txn_id, payload = make_async_payload(first_name, last_name)
    print(f"  transaction_id  : {txn_id}")
    print(f"  sender_uri      : {CALLBACK_URL}")

    hdrs   = {"Content-Type": "application/json",
               "Authorization": f"Bearer {token}"}
    t_sent = time.time()

    try:
        r = requests.post(ASYNC_URL, json=payload, headers=hdrs, timeout=30)
    except requests.exceptions.ConnectionError as e:
        err(f"Connection error: {e}")
        sys.exit(1)

    print()
    print(f"  HTTP Status : {r.status_code}  ", end="")
    if r.status_code == 202:
        print("[OK] Correct - immediate ACK, no data yet (async accepted)")
    elif r.status_code == 200:
        warn("Got 200 instead of 202 - check async endpoint")
    else:
        err(f"Unexpected status {r.status_code}")
        print(f"  Body: {r.text[:300]}")

    try:
        ack = r.json()
        dump_json(ack, "Async ACK Response")
        ack_action = ack.get("header", {}).get("action", "?")
        ack_status = ack.get("header", {}).get("status", "?")
        ack_sr     = ack.get("message", {}).get("search_response", "NOT_PRESENT")
        print(f"  ACK action  : {ack_action}  {'[OK]' if ack_action == 'on-search' else '[ERR]'}")
        print(f"  ACK status  : {ack_status}")
        if ack_sr == []:
            print(f"  ACK data    : empty [] - correct, results come via callback")
        else:
            print(f"  ACK data    : {ack_sr}")
    except Exception:
        warn("Could not parse ACK JSON")
    sep()

    # -- Step 4: Wait for callback push ----------------------------------------
    info(f"Step 4/5 - Waiting up to {TIMEOUT_SEC}s for openIMIS to push farmer results...")
    print(f"  [watching {CALLBACK_URL}]")

    arrived = _callback_received.wait(timeout=TIMEOUT_SEC)
    elapsed = round(time.time() - t_sent, 2)

    print()
    if arrived:
        ok(f"Callback received! ({elapsed}s after request)")
        with _callback_lock:
            cb_data = dict(_callback_payload)

        arrived_at = cb_data.pop("_arrived_at", "?")
        raw_json   = cb_data.pop("_raw_json", None)
        print(f"  Arrived at  : {arrived_at}")

        sr       = cb_data.get("message", {}).get("search_response", [])
        records  = sr[0].get("data", {}).get("reg_records", []) if sr else []
        pag      = sr[0].get("pagination", {}) if sr else {}
        reg_type = sr[0].get("data", {}).get("reg_type", "?") if sr else "?"
        rec_type = sr[0].get("data", {}).get("reg_record_type", "?") if sr else "?"

        print(f"  reg_type    : {reg_type}")
        print(f"  rec_type    : {rec_type}")
        print(f"  Records     : {len(records)}  "
              f"(page_size={pag.get('page_size')}  total={pag.get('total_count')})")

        # Display farmer records
        show_farmer_records(records, "Callback Push - Farmer Records")

        # SPDCI compliance checks
        all_ok = verify_callback_payload(cb_data)
        print()
        if all_ok:
            ok("Callback payload is fully SPDCI-compliant")
        else:
            err("Some SPDCI compliance checks failed")

        # Full JSON dump
        dump_json(cb_data, "Full Callback JSON Response (Farmer Registry)")

    else:
        err(f"No callback received within {TIMEOUT_SEC}s!")
        warn("Possible reasons:")
        warn("  * openIMIS server crashed or is unreachable")
        warn("  * sender_uri blocked by firewall")
        warn("  * Background task failed (check: tail -f /tmp/django_server.log)")
    sep()

    # -- Step 5: Poll txn/status -----------------------------------------------
    info("Step 5/5 - Polling /reg/txn/status (alternate retrieval path)...")
    print(f"  Polling every {POLL_INTERVAL}s  (up to {POLL_INTERVAL * 5}s)...")
    print()
    poll_result = poll_txn_status(txn_id, token, max_polls=5)

    print()
    if poll_result:
        poll_status = poll_result.get("header", {}).get("status", "?")
        if poll_status == "succ":
            ok("txn/status returned 'succ'")
            sr      = poll_result.get("message", {}).get("search_response", [])
            records = sr[0].get("data", {}).get("reg_records", []) if sr else []
            show_farmer_records(records, "txn/status - Farmer Records")
            dump_json(poll_result, "Full txn/status JSON Response (Farmer Registry)")
        elif poll_status == "pdng":
            warn("txn/status still 'pdng' - search is slow or stuck")
        else:
            err(f"txn/status returned: {poll_status}")
            print(json.dumps(poll_result, indent=2, default=str))
    else:
        err("Could not retrieve result via txn/status")

    # -- Summary ---------------------------------------------------------------
    print()
    print("="*58)
    print("  Summary")
    print("="*58)
    print(f"  Registry type           : Farmer (FRPerson)")
    print(f"  Async ACK (HTTP 202)    : {'[OK]' if r.status_code == 202 else '[FAIL]'}")
    print(f"  Callback push received  : {'[OK] ' + str(elapsed) + 's' if arrived else '[FAIL] timed out'}")
    print(f"  txn/status polling      : {'[OK]' if poll_result and poll_result.get('header', {}).get('status') == 'succ' else '[FAIL]'}")
    print("="*58)
    print()

    server.shutdown()


if __name__ == "__main__":
    main()
