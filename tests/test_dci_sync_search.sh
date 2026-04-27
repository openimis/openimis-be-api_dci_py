#!/bin/bash

# Test DCI Sync Search Endpoint
# This script sends a DCI-compliant search request to the OpenIMIS API.

# Configuration
BASE_URL="http://localhost:8000"
ENDPOINT="/api/dci/reg/sync/search"
TOKEN="your_token_here" # If authentication is required

# Sample Payload
# Looking for firstName: John, lastName: Doe
PAYLOAD=$(cat <<EOF
{
    "signature": "Signature: fake-signature-for-testing",
    "header": {
        "version": "1.0.0",
        "message_id": "$(date +%s)",
        "message_ts": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
        "action": "search",
        "sender_id": "test-sender",
        "receiver_id": "openimis",
        "sender_uri": "http://localhost:8000/callback"
    },
    "message": {
        "transaction_id": "trans-$(date +%s)",
        "search_request": [
            {
                "reference_id": "ref-$(date +%s)",
                "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
                "search_criteria": {
                    "reg_type": "person",
                    "query_type": "sync",
                    "query": {
                        "value": {
                            "expression": {
                                "query": {
                                    "\$and": [
                                        {"firstName": {"\$eq": "John"}},
                                        {"lastName": {"\$eq": "Doe"}},
                                        {"gender": {"\$eq": "Male"}},
                                        {"dob": {"\$eq": "1980-01-01"}},
                                        {"phone": {"\$eq": "123456789"}},
                                        {"email": {"\$eq": "john.doe@example.com"}}
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
EOF
)

echo "Sending search request to ${BASE_URL}${ENDPOINT}..."
echo "Payload: ${PAYLOAD}"
echo "-----------------------------------"

curl -X POST "${BASE_URL}${ENDPOINT}" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer ${TOKEN}" \
     -d "${PAYLOAD}" | python3 -m json.tool
