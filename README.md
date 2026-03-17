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

### Supported SPDCI Standards

This module implements the following SPDCI (Social Protection Digital Convergence Initiative) registry standards:

- **IBR (Integrated Beneficiary Registry)** - Person registry following SPDCI DO.IBR.01 specification
- **FR (Farmer Registry)** - Farmer/agricultural registry (planned)

### Implemented Endpoints

#### Person Registry (IBR)
- `POST /api/api_dci/registry/sync/search` - Synchronous search for Person records
- `GET /api/api_dci/registry/person/{id}` - Retrieve a single Person by ID
- `POST /api/api_dci/login/` - JWT authentication endpoint

#### Planned Endpoints
- `POST /api/api_dci/registry/search` - Asynchronous search (FR standard)
- `POST /api/api_dci/registry/subscribe` - Event subscription
- `POST /api/api_dci/registry/notify` - Event notifications
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

## SPDCI Compliance

### Person Data Object (DO.IBR.01)

The module implements strict SPDCI DO.IBR.01 Person Data Object specification:

**Specification**: [SPDCI DO.IBR.01 Person](https://standards.spdci.org/standards/wip-integrated-beneficiary-registry-v1.0.0/ibr/1.-crvs/data/data-objects/do.ibr.01-person)

| SPDCI Field | Type | OpenIMIS Field | Notes |
|------------|------|----------------|-------|
| `identifier` | array | `uuid`, `id` | Array of {type, value, system} objects |
| `name` | object | `first_name`, `last_name` | Object with given_name, family_name, full_name |
| `birth_date` | datetime | `dob` | ISO 8601 datetime format (YYYY-MM-DDTHH:MM:SSZ) |
| `sex` | enum | `gender.code` | Values: "male", "female", "others", "unknown" |
| `phone_number` | array | `phone`, `json_ext` | Array of phone numbers (E.164 recommended) |
| `email` | array | `email`, `json_ext` | Array of email addresses |
| `address` | array | `location`, `json_ext` | Array of address objects (DO.COM.03) |
| `registration_date` | datetime | `date_created` | ISO 8601 format |
| `last_updated` | datetime | `date_updated` | ISO 8601 format |

### Multi-Standard Architecture

The module supports multiple SPDCI registry standards through a flexible endpoint structure:

```
/api/api_dci/
├── registry/
│   ├── sync/search     # IBR synchronous search (simple queries)
│   ├── search          # FR asynchronous search (complex queries with expressions)
│   ├── person/{id}     # IBR direct person lookup
│   ├── subscribe       # FR event subscriptions
│   └── notify          # FR event notifications
└── login/              # JWT authentication
```

#### Query Type Support

**IBR Standard** (`/registry/sync/search`):
- Query type: `sync`
- Simple field-based queries
- Synchronous response with immediate results

**FR Standard** (`/registry/search`):
- Query types: `expression`, `predicate`, `idtype-value`
- Complex query expressions
- Asynchronous pattern with callbacks

Both standards share the same Person data object schema (DO.IBR.01) for consistency.

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

### Search Response (SPDCI DO.IBR.01 Format)

```json
{
  "signature": "Signature: namespace=\"spdci\", kidId=\"...\", algorithm=\"ed25519\", headers=\"...\", signature=\"...\"",
  "header": {
    "version": "1.0.0",
    "message_id": "response-uuid-1234",
    "message_ts": "2026-02-20T23:54:01.123456Z",
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

### SPDCI Compliance Testing

This module can be tested for SPDCI standard compliance using the OpenSPP compliance test suite:

**Documentation**: [Testing Your Registry](https://github.com/OpenSPP/spdci-compliance/blob/fix/align-configs-with-spec/docs/testing-your-registry.md)

#### Setup Compliance Tests

1. Clone the SPDCI compliance repository:
```bash
git clone https://github.com/OpenSPP/spdci-compliance.git
cd spdci-compliance
npm install
```

2. Configure the test environment:
```bash
export API_BASE_URL=http://localhost/api/api_dci/
export DCI_AUTH_TOKEN="Bearer YOUR_JWT_TOKEN"
export DOMAIN=ibr  # or 'fr' for Farmer Registry
```

3. Run compliance tests:
```bash
# Test IBR (Integrated Beneficiary Registry) compliance
npm run test:ibr

# Test FR (Farmer Registry) compliance
npm run test:fr

# Run specific test
npx cucumber-js --tags "@req=FR-CORE-RG-SYNC-SEARCH-EXTRA-01"
```

#### Getting Authentication Token

```bash
curl -X POST http://localhost/api/api_dci/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin123"}'
```

#### Docker-based Testing

If using the OpenIMIS Docker setup with the SPDCI compliance container:

```bash
docker exec -it openimis-dist_dkr-spdci-compliance-1 sh -c \
  'DCI_AUTH_TOKEN="Bearer YOUR_TOKEN" \
   API_BASE_URL=http://openimis-dist_dkr-backend-1:8000/api/api_dci/ \
   DOMAIN=ibr \
   npx cucumber-js --tags "@smoke"'
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run compliance tests to ensure SPDCI standard conformity
5. Submit a pull request

## License

GNU Affero General Public License v3.0

## Links

- [OpenIMIS Website](https://openimis.org/)
- [DCI Specification](https://api.spdci.org/)
- [OpenIMIS GitHub](https://github.com/openimis)