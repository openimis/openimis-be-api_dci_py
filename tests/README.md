# DCI Module — Integration Tests

These scripts test the live DCI API endpoints against a running openIMIS server.  
They are **integration tests**, not unit tests — they require the server to be up.

## Prerequisites

```bash
# Start the server
source "/Users/hisoka/scripts/untitled folder/openimis2410.sh"
```

## Test Scripts

| Script | What it tests |
|--------|--------------|
| `test_dci_quick.py` | Sync search — quick interactive check with real DB names |
| `test_dci_sync_full.py` | Sync search — 7 exhaustive SPDCI spec checks |
| `test_dci_async.py` | Async search — full end-to-end: 202 ACK + callback push + txn/status poll |
| `test_dci_sync_search.py` | Original basic sync/async smoke test |

## Usage

```bash
cd tests/

# Quick sync test (real names from your DB)
python3 test_dci_quick.py           # all records
python3 test_dci_quick.py Ana       # by first name
python3 test_dci_quick.py Ana Ali   # by first + last name

# Full SPDCI spec validation (sync)
python3 test_dci_sync_full.py

# Full async end-to-end (202 ACK + callback push + polling)
python3 test_dci_async.py
python3 test_dci_async.py Ana
python3 test_dci_async.py Ana Ali
```

## What async test does

```
You → openIMIS  POST /reg/search          → HTTP 202 ACK  (instant)
openIMIS (bg)  → Your callback :8099      → Full results pushed (~1-2s)
You → openIMIS  POST /reg/txn/status      → status: succ
```

The script starts a mock callback server on port **8099** automatically.
