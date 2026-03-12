# OpenIMIS Backend DCI API Module

## Overview

This module provides a REST API for OpenIMIS following the **DCI (Digital Convergence Initiative)** standard for social protection data exchange. It enables interoperability between OpenIMIS and other systems that implement the DCI specification.

## DCI Standard

The DCI (Digital Convergence Initiative) is a standard for sharing information in the context of social protection. It defines:

- Data object schemas (Person, Household, etc.)
- API endpoints for synchronization
- Message formats for request/response

### References

- DCI Registry Core API: https://api.spdci.org/release/html/registry_core_api_v1.0.0.html
- DCI Person Schema: https://schema.spdci.org/core/v1/data/Person.jsonld

## Features

### Implemented Endpoints

- `POST /api/dci/reg/sync/search` - Synchronous search for Person records following DCI standard
- `POST /api/dci/reg/search` - Asynchronous search for Person records following DCI standard

## Installation

### Requirements

- Python 3.6+
- Django 2.1+
- Django REST Framework
- drf-spectacular (for OpenAPI documentation)
- openimis-be-core
- openimis-be-individual

### Setup

1. Install the module:
```bash
pip install openimis-be-api_dci
```

2. Add to your OpenIMIS configuration (`openimis.json`):
```json
{
  "modules": [
    {
      "name": "api_dci",
      "pip": "openimis-be-api_dci"
    }
  ]
}
```

3. The module will be automatically loaded by OpenIMIS.

## API Documentation

Once installed, access the API documentation at:

- OpenAPI Schema: `/api/dci/docs/`
- Swagger UI: `/api/dci/docs/swagger/`
- ReDoc: `/api/dci/docs/redoc/`

## DCI Person Mapping

The module maps DCI Person objects to OpenIMIS Individual records:

| DCI Field | OpenIMIS Field | Notes |
|-----------|---------------|-------|
| `@type` | - | Constant: "Person" |
| `id` | `uuid` | Format: `openimis:individual:{uuid}` |
| `firstName` | `first_name` | Direct mapping |
| `lastName` | `last_name` | Direct mapping |
| `dob` | `dob` | ISO 8601 format |
| `gender` | `gender.code` | M→Male, F→Female, O→Other |
| `phone` | `phone` | Direct mapping |
| `email` | `email` | Direct mapping |

## Example Usage

### Search Request

```bash
POST /api/dci/reg/sync/search
Content-Type: application/json
Authorization: Bearer <token>

{
  "signature": "Signature: namespace=\"spdci\", kidId=\"...\", algorithm=\"ed25519\", headers=\"...\", signature=\"...\"",
  "header": {
    "version": "1.0.0",
    "message_id": "uuid-1234",
    "message_ts": "2026-02-20T23:54:00Z",
    "action": "search",
    "sender_id": "external-system",
    "receiver_id": "openimis",
    "sender_uri": "https://callback.example.com",
    "is_msg_encrypted": false
  },
  "message": {
    "transaction_id": "tx-5678",
    "search_request": [
      {
        "reference_id": "ref-111",
        "timestamp": "2026-02-20T23:54:00Z",
        "search_criteria": {
          "reg_type": "person",
          "query_type": "sync",
          "query": {
            "type": "ns:org:QueryType:expression",
            "value": {
              "expression": {
                "query": {
                  "$and": [
                    {"firstName": {"$eq": "John"}},
                    {"lastName": {"$eq": "Doe"}}
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
```

### Search Response

```json
{
  "signature": "Signature: namespace=\"spdci\", kidId=\"...\", algorithm=\"ed25519\", headers=\"...\", signature=\"...\"",
  "header": {
    "version": "1.0.0",
    "message_id": "uuid-response",
    "message_ts": "2026-02-20T23:54:01Z",
    "action": "on-search",
    "status": "success",
    "sender_id": "openimis",
    "receiver_id": "external-system",
    "sender_uri": "https://callback.example.com",
    "total_count": 1,
    "is_msg_encrypted": false,
    "meta": {}
  },
  "message": {
    "transaction_id": "tx-5678",
    "search_response": [
      {
        "reference_id": "ref-111",
        "timestamp": "2026-02-20T23:54:01Z",
        "status": "succ",
        "status_reason_code": "succ",
        "status_reason_message": "Success",
        "registry_data": {
          "data": [
            {
              "@type": "Person",
              "id": "openimis:individual:12345",
              "firstName": "John",
              "lastName": "Doe",
              "dob": "1990-01-15",
              "gender": "Male"
            }
          ]
        }
      }
    ]
  }
}
```

## Permissions

The module uses OpenIMIS Individual permissions:

- **Search**: `individual.gql_query_individuals_perms`
- **Create**: `individual.gql_mutation_create_individuals_perms`
- **Update**: `individual.gql_mutation_update_individuals_perms`
- **Delete**: `individual.gql_mutation_delete_individuals_perms`

## Module Structure

```
openimis-be-api_dci_py/
├── api_dci/
│   ├── __init__.py
│   ├── apps.py              # Django app configuration
│   ├── urls.py              # URL routing
│   ├── permissions.py       # Permission classes
│   ├── serializers/         # DCI serializers
│   │   ├── __init__.py
│   │   └── person_serializer.py
│   ├── views/               # API views
│   │   ├── __init__.py
│   │   └── person_viewset.py
│   ├── converters/          # Data converters
│   │   ├── __init__.py
│   │   └── person_converter.py
│   └── tests/               # Unit tests
│       └── __init__.py
├── setup.py
└── README.md
```

## Development

### Running Tests

```bash
python -m pytest api_dci/tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

GNU Affero General Public License v3.0

## Links

- [OpenIMIS Website](https://openimis.org/)
- [DCI Specification](https://api.spdci.org/)
- [OpenIMIS GitHub](https://github.com/openimis)