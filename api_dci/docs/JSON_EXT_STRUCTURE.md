# Individual json_ext Structure for SPDCI Registry Types

This document describes the structure of the `Individual.json_ext` field for storing SPDCI-specific data that doesn't fit in standard Individual model fields.

## Overview

The `json_ext` field stores registry-specific data based on the `SPDCI_REGISTRY_TYPE` environment variable:
- **FR** (Farmer Registry): Agricultural and farming data
- **SR** (Social Registry): Social protection and household data
- **IBR** (Integrated Beneficiary Registry): Beneficiary and program data

## Common Structure

All registry types share a common base structure:

```json
{
  "registry_type": "FR|SR|IBR",
  "registry_metadata": {
    "source_system": "string",
    "external_id": "string",
    "last_sync": "ISO8601 datetime"
  },
  "spdci_data": {
    // Registry-specific data (see below)
  }
}
```

## FR (Farmer Registry) Structure

Based on **SPDCI DO.FR.04 Farmer** specification.

```json
{
  "registry_type": "FR",
  "registry_metadata": {
    "source_system": "external-farmer-registry",
    "external_id": "FARMER-12345",
    "last_sync": "2026-03-23T10:00:00Z"
  },
  "spdci_data": {
    "farmer_personal_details": {
      // DO.FR.02 Member
      "member_identifier": "string",
      "farmer_status": "active|inactive",
      "occupation": "string",
      "education_level": "string"
    },
    "family_details": {
      // DO.FR.03 Group
      "group_identifier": "string",
      "group_type": "household|family",
      "group_size": 5,
      "poverty_score": 45.5,
      "group_head_info": {
        "name": "string",
        "identifier": "string"
      },
      "members": [
        {
          "identifier": "string",
          "name": "string",
          "relationship": "spouse|child|parent|other",
          "age": 30
        }
      ]
    },
    "farm_details": [
      // DO.FR.05 FarmInfo (array - multiple farms)
      {
        "farm_id": "string",
        "farm_type": "crop|livestock|mixed|agroforestry",
        "location": {
          "latitude": -1.2921,
          "longitude": 36.8219,
          "address": "string",
          "place_name": "string"
        },
        "land_tenure": "owned|rented|leased|communal|customary",
        "land_size": 10.5,
        "unit": "hectares|acres|square_meters",
        "farming_activities": [
          // DO.FR.06 FarmingActivities
          {
            "activity_type": "crop|livestock|agroforestry",
            "crop_details": {
              // DO.FR.07 CropDetails
              "crop_type": "maize|wheat|rice|vegetables",
              "crop_variety": "string",
              "area_planted": 5.0,
              "unit": "hectares",
              "planting_date": "2026-01-15",
              "expected_harvest_date": "2026-06-15",
              "irrigation_method": "rainfed|irrigated|drip"
            },
            "livestock_details": {
              // DO.FR.08 LivestockDetails
              "livestock_type": "cattle|goats|sheep|poultry",
              "number_of_animals": 20,
              "breed": "string",
              "production_purpose": "meat|milk|eggs|breeding"
            }
          }
        ],
        "registration_date": "2026-01-01T00:00:00Z",
        "last_updated": "2026-03-20T00:00:00Z"
      }
    ],
    "machineries_details": [
      // DO.FR.09 Machinery (array - multiple equipment)
      {
        "machinery_id": "string",
        "machinery_type": "tractor|harvester|plough|sprayer",
        "model": "string",
        "year_of_purchase": 2020,
        "ownership_status": "owned|rented|shared",
        "condition": "good|fair|poor"
      }
    ],
    "additional_attributes": [
      // Country-specific attributes
      {
        "key": "string",
        "value": "string|number|boolean"
      }
    ],
    "registration_date": "2026-01-01T00:00:00Z",
    "last_updated": "2026-03-23T10:00:00Z"
  }
}
```

## SR (Social Registry) Structure

Based on **SPDCI DO.SR.01 Person** specification.

```json
{
  "registry_type": "SR",
  "registry_metadata": {
    "source_system": "external-social-registry",
    "external_id": "SR-67890",
    "last_sync": "2026-03-23T10:00:00Z"
  },
  "spdci_data": {
    "household_details": {
      "household_id": "string",
      "household_size": 6,
      "head_of_household": {
        "name": "string",
        "identifier": "string",
        "relationship": "self|spouse|parent"
      },
      "members": [
        {
          "identifier": "string",
          "name": "string",
          "relationship": "spouse|child|parent|sibling|other",
          "age": 25,
          "education_level": "none|primary|secondary|tertiary",
          "employment_status": "employed|unemployed|self_employed|student"
        }
      ]
    },
    "socio_economic_details": {
      "poverty_score": 35.5,
      "income_level": "low|medium|high",
      "monthly_income": 15000.0,
      "currency": "USD",
      "housing_type": "owned|rented|informal",
      "access_to_services": {
        "electricity": true,
        "water": true,
        "sanitation": true,
        "healthcare": false
      }
    },
    "vulnerability_details": {
      "disability_status": true,
      "disability_type": "physical|visual|hearing|intellectual",
      "chronic_illness": false,
      "vulnerable_groups": ["elderly", "single_parent"]
    },
    "program_enrollment": [
      {
        "program_id": "string",
        "program_name": "Cash Transfer Program",
        "enrollment_date": "2025-06-01",
        "status": "active|inactive|suspended",
        "benefit_amount": 5000.0
      }
    ],
    "additional_attributes": [
      {
        "key": "string",
        "value": "string|number|boolean"
      }
    ],
    "registration_date": "2025-01-01T00:00:00Z",
    "last_updated": "2026-03-23T10:00:00Z"
  }
}
```

## IBR (Integrated Beneficiary Registry) Structure

Based on **SPDCI DO.IBR.01 Person** specification.

```json
{
  "registry_type": "IBR",
  "registry_metadata": {
    "source_system": "external-ibr",
    "external_id": "IBR-11111",
    "last_sync": "2026-03-23T10:00:00Z"
  },
  "spdci_data": {
    "beneficiary_details": {
      "beneficiary_id": "string",
      "beneficiary_type": "individual|household|group",
      "eligibility_status": "eligible|ineligible|pending",
      "eligibility_criteria": [
        {
          "criterion": "income_threshold",
          "value": true,
          "verified_date": "2026-01-15"
        }
      ]
    },
    "program_participation": [
      {
        "program_id": "string",
        "program_name": "Health Insurance",
        "program_type": "health|education|cash_transfer|food_security",
        "enrollment_date": "2025-08-01",
        "status": "active|inactive|suspended|completed",
        "benefit_details": {
          "benefit_type": "cash|voucher|service|in_kind",
          "amount": 10000.0,
          "currency": "USD",
          "frequency": "monthly|quarterly|one_time",
          "payment_method": "bank_transfer|mobile_money|cash"
        },
        "payment_history": [
          {
            "payment_date": "2026-03-01",
            "amount": 10000.0,
            "status": "completed|pending|failed"
          }
        ]
      }
    ],
    "verification_details": {
      "verification_status": "verified|unverified|pending",
      "verification_date": "2026-01-20",
      "verification_method": "document|biometric|home_visit",
      "verified_by": "officer_name"
    },
    "additional_attributes": [
      {
        "key": "string",
        "value": "string|number|boolean"
      }
    ],
    "registration_date": "2025-01-01T00:00:00Z",
    "last_updated": "2026-03-23T10:00:00Z"
  }
}
```

## Field Mapping Notes

### Standard Individual Model Fields

These fields map directly to `Individual` model fields (not stored in json_ext):

| SPDCI Field | Individual Field | Notes |
|-------------|------------------|-------|
| name.given_name | first_name | Direct mapping |
| name.family_name | last_name | Direct mapping |
| birth_date | dob | Convert ISO datetime to date |
| sex | gender (via Gender model) | Map: male→M, female→F, others→O |
| phone_number[0] | phone | Take first phone number |
| email[0] | email | Take first email |
| address | location (via Location model) | Requires location lookup/creation |

### json_ext Storage

Store in json_ext when:
1. No corresponding Individual model field exists
2. Multiple values (arrays) and Individual field is single-value
3. Registry-specific data (FR farm_details, SR poverty_score, etc.)
4. Nested objects that don't fit the Individual model structure

## Implementation Guidelines

### Creating Individual from SPDCI Data

```python
from api_dci.utils.json_ext_manager import JsonExtManager

# Determine registry type
registry_type = get_registry_type()  # FR, SR, or IBR

# Parse SPDCI person data
base_data = PersonConverter.dci_person_to_individual_data(spdci_person)

# Extract and structure registry-specific data
json_ext = JsonExtManager.structure_json_ext(
    registry_type=registry_type,
    spdci_person=spdci_person,
    metadata={
        'source_system': 'external-system',
        'external_id': 'EXT-12345'
    }
)

# Create Individual
individual = Individual.objects.create(
    **base_data,
    json_ext=json_ext
)
```

### Reading Registry-Specific Data

```python
# Get registry-specific data
spdci_data = individual.json_ext.get('spdci_data', {})

if individual.json_ext.get('registry_type') == 'FR':
    farm_details = spdci_data.get('farm_details', [])
    for farm in farm_details:
        print(f"Farm size: {farm.get('land_size')} {farm.get('unit')}")
```

## Validation Rules

1. **registry_type** must match `SPDCI_REGISTRY_TYPE` environment variable
2. **spdci_data** must conform to the corresponding SPDCI data object schema
3. All dates must be ISO 8601 format
4. Enumerations must use lowercase values (e.g., "male" not "Male")
5. Numeric values (land_size, poverty_score) must be valid numbers
6. Arrays (farm_details, machineries_details) must be valid JSON arrays

## Migration Considerations

When changing `SPDCI_REGISTRY_TYPE`:
1. Existing `json_ext` data remains unchanged
2. New records use the new registry_type structure
3. Consider data migration scripts if switching registry type for existing installation
4. Query filters should check both `registry_type` and data structure

## Future Enhancements

- Add json_ext validation at model level
- Create Django management commands for data migration
- Add indexing for frequently queried json_ext fields (PostgreSQL JSONB)
- Create utility functions for common json_ext queries
