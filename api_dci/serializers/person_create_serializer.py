"""
Person Create/Update Serializers

Serializers for creating and updating Person/Individual records from SPDCI data.
Supports FR (Farmer Registry), SR (Social Registry), and IBR (Integrated Beneficiary Registry).
"""
from rest_framework import serializers
from datetime import datetime


class FarmerPersonalDetailsSerializer(serializers.Serializer):
    """DO.FR.02 Member - Farmer personal details"""
    member_identifier = serializers.CharField(max_length=255, required=False)
    farmer_status = serializers.CharField(max_length=50, required=False)
    occupation = serializers.CharField(max_length=255, required=False)
    education_level = serializers.CharField(max_length=100, required=False)


class FamilyDetailsSerializer(serializers.Serializer):
    """DO.FR.03 Group - Family/household details"""
    group_identifier = serializers.CharField(max_length=255, required=False)
    group_type = serializers.CharField(max_length=50, required=False)
    group_size = serializers.IntegerField(required=False, allow_null=True)
    poverty_score = serializers.FloatField(required=False, allow_null=True)
    group_head_info = serializers.DictField(required=False)
    members = serializers.ListField(child=serializers.DictField(), required=False)


class FarmDetailsSerializer(serializers.Serializer):
    """DO.FR.05 FarmInfo - Farm details"""
    farm_id = serializers.CharField(max_length=255, required=False)
    farm_type = serializers.CharField(max_length=50, required=False)
    location = serializers.DictField(required=False)
    land_tenure = serializers.CharField(max_length=50, required=False)
    land_size = serializers.FloatField(required=False, allow_null=True)
    unit = serializers.CharField(max_length=50, required=False)
    farming_activities = serializers.ListField(child=serializers.DictField(), required=False)
    registration_date = serializers.DateTimeField(required=False, allow_null=True)
    last_updated = serializers.DateTimeField(required=False, allow_null=True)


class MachineriesDetailsSerializer(serializers.Serializer):
    """DO.FR.09 Machinery - Machinery details"""
    machinery_id = serializers.CharField(max_length=255, required=False)
    machinery_type = serializers.CharField(max_length=100, required=False)
    model = serializers.CharField(max_length=255, required=False)
    year_of_purchase = serializers.IntegerField(required=False, allow_null=True)
    ownership_status = serializers.CharField(max_length=50, required=False)
    condition = serializers.CharField(max_length=50, required=False)


class HouseholdDetailsSerializer(serializers.Serializer):
    """SR - Household details"""
    household_id = serializers.CharField(max_length=255, required=False)
    household_size = serializers.IntegerField(required=False, allow_null=True)
    head_of_household = serializers.DictField(required=False)
    members = serializers.ListField(child=serializers.DictField(), required=False)


class SocioEconomicDetailsSerializer(serializers.Serializer):
    """SR - Socio-economic details"""
    poverty_score = serializers.FloatField(required=False, allow_null=True)
    income_level = serializers.CharField(max_length=50, required=False)
    monthly_income = serializers.FloatField(required=False, allow_null=True)
    currency = serializers.CharField(max_length=10, required=False)
    housing_type = serializers.CharField(max_length=50, required=False)
    access_to_services = serializers.DictField(required=False)


class VulnerabilityDetailsSerializer(serializers.Serializer):
    """SR - Vulnerability details"""
    disability_status = serializers.BooleanField(required=False)
    disability_type = serializers.CharField(max_length=100, required=False)
    chronic_illness = serializers.BooleanField(required=False)
    vulnerable_groups = serializers.ListField(child=serializers.CharField(), required=False)


class BeneficiaryDetailsSerializer(serializers.Serializer):
    """IBR - Beneficiary details"""
    beneficiary_id = serializers.CharField(max_length=255, required=False)
    beneficiary_type = serializers.CharField(max_length=50, required=False)
    eligibility_status = serializers.CharField(max_length=50, required=False)
    eligibility_criteria = serializers.ListField(child=serializers.DictField(), required=False)


class ProgramParticipationSerializer(serializers.Serializer):
    """IBR - Program participation"""
    program_id = serializers.CharField(max_length=255, required=False)
    program_name = serializers.CharField(max_length=255, required=False)
    program_type = serializers.CharField(max_length=100, required=False)
    enrollment_date = serializers.DateField(required=False, allow_null=True)
    status = serializers.CharField(max_length=50, required=False)
    benefit_details = serializers.DictField(required=False)
    payment_history = serializers.ListField(child=serializers.DictField(), required=False)


class VerificationDetailsSerializer(serializers.Serializer):
    """IBR - Verification details"""
    verification_status = serializers.CharField(max_length=50, required=False)
    verification_date = serializers.DateField(required=False, allow_null=True)
    verification_method = serializers.CharField(max_length=100, required=False)
    verified_by = serializers.CharField(max_length=255, required=False)


class DCIPersonCreateSerializer(serializers.Serializer):
    """
    SPDCI Person Create/Update Serializer

    Accepts SPDCI Person data (DO.COM.01 base + FR/SR/IBR extensions)
    and prepares data for Individual model creation/update.
    """
    # DO.COM.01 Person base fields
    identifier = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="Array of identifiers (DO.COM.01 Identifier)"
    )
    name = serializers.DictField(
        required=False,
        help_text="Person name (DO.COM.02 Name)"
    )
    birth_date = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Birth date in ISO 8601 format"
    )
    sex = serializers.CharField(
        max_length=20,
        required=False,
        help_text="Sex: male, female, others, unknown"
    )
    phone_number = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Array of phone numbers"
    )
    email = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Array of email addresses"
    )
    address = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="Array of addresses (DO.COM.03 Address)"
    )

    # FR (Farmer Registry) specific fields
    farmer_personal_details = FarmerPersonalDetailsSerializer(required=False)
    family_details = FamilyDetailsSerializer(required=False)
    farm_details = serializers.ListField(
        child=FarmDetailsSerializer(),
        required=False,
        help_text="Array of farm details (DO.FR.05 FarmInfo)"
    )
    machineries_details = serializers.ListField(
        child=MachineriesDetailsSerializer(),
        required=False,
        help_text="Array of machinery details (DO.FR.09 Machinery)"
    )

    # SR (Social Registry) specific fields
    household_details = HouseholdDetailsSerializer(required=False)
    socio_economic_details = SocioEconomicDetailsSerializer(required=False)
    vulnerability_details = VulnerabilityDetailsSerializer(required=False)
    program_enrollment = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="Array of program enrollment records"
    )

    # IBR (Integrated Beneficiary Registry) specific fields
    beneficiary_details = BeneficiaryDetailsSerializer(required=False)
    program_participation = serializers.ListField(
        child=ProgramParticipationSerializer(),
        required=False,
        help_text="Array of program participation records"
    )
    verification_details = VerificationDetailsSerializer(required=False)

    # Common fields
    additional_attributes = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="Country-specific attributes"
    )
    registration_date = serializers.DateTimeField(required=False, allow_null=True)
    last_updated = serializers.DateTimeField(required=False, allow_null=True)

    def validate_sex(self, value):
        """Validate sex enumeration"""
        valid_values = ['male', 'female', 'others', 'unknown']
        if value and value.lower() not in valid_values:
            raise serializers.ValidationError(
                f"Invalid sex value. Must be one of: {', '.join(valid_values)}"
            )
        return value.lower() if value else value

    def validate(self, data):
        """
        Validate Person data - ensure at least name or identifier is provided
        """
        if not data.get('name') and not data.get('identifier'):
            raise serializers.ValidationError(
                "At least 'name' or 'identifier' must be provided"
            )
        return data


class DCIPersonCreateRequestSerializer(serializers.Serializer):
    """
    Complete SPDCI Person create request
    POST /api/api_dci/registry/person
    """
    signature = serializers.JSONField(required=False, allow_null=True)
    header = serializers.DictField()
    message = serializers.DictField()

    def validate_message(self, value):
        """Validate message contains person data"""
        if 'person' not in value:
            raise serializers.ValidationError("Message must contain 'person' field")

        # Validate person data
        person_serializer = DCIPersonCreateSerializer(data=value['person'])
        if not person_serializer.is_valid():
            raise serializers.ValidationError({
                'person': person_serializer.errors
            })

        return value


class DCIPersonUpdateRequestSerializer(serializers.Serializer):
    """
    Complete SPDCI Person update request
    PUT /api/api_dci/registry/person/{id}
    """
    signature = serializers.JSONField(required=False, allow_null=True)
    header = serializers.DictField()
    message = serializers.DictField()

    def validate_message(self, value):
        """Validate message contains person data"""
        if 'person' not in value:
            raise serializers.ValidationError("Message must contain 'person' field")

        # Validate person data (allow partial updates)
        person_serializer = DCIPersonCreateSerializer(
            data=value['person'],
            partial=True
        )
        if not person_serializer.is_valid():
            raise serializers.ValidationError({
                'person': person_serializer.errors
            })

        return value


class DCIPersonResponseSerializer(serializers.Serializer):
    """
    SPDCI Person create/update response
    """
    @classmethod
    def create_success_response(cls, request_data, person_id, operation="create"):
        """
        Create success response for person create/update.

        Args:
            request_data: Original request data dict
            person_id: Created/updated person ID
            operation: "create" or "update"

        Returns:
            dict: SPDCI response
        """
        action_map = {
            'create': 'on-create',
            'update': 'on-update'
        }

        return {
            'signature': request_data.get('signature', ""),
            'header': {
                'version': '1.0.0',
                'message_id': f"response-{request_data['header']['message_id']}",
                'message_ts': datetime.utcnow().isoformat() + 'Z',
                'action': action_map.get(operation, 'on-create'),
                'status': 'succ',
                'sender_id': request_data['header'].get('receiver_id', 'openimis'),
                'receiver_id': request_data['header']['sender_id'],
                'is_msg_encrypted': request_data['header'].get('is_msg_encrypted', False),
            },
            'message': {
                'transaction_id': request_data.get('message', {}).get('transaction_id', ''),
                'person_id': person_id,
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        }

    @classmethod
    def create_error_response(cls, request_data, error_message, operation="create"):
        """
        Create error response for person create/update.

        Args:
            request_data: Original request data dict
            error_message: Error description
            operation: "create" or "update"

        Returns:
            dict: SPDCI error response
        """
        action_map = {
            'create': 'on-create',
            'update': 'on-update'
        }

        return {
            'signature': request_data.get('signature', ""),
            'header': {
                'version': '1.0.0',
                'message_id': f"response-{request_data.get('header', {}).get('message_id', 'unknown')}",
                'message_ts': datetime.utcnow().isoformat() + 'Z',
                'action': action_map.get(operation, 'on-create'),
                'status': 'error',
                'sender_id': request_data.get('header', {}).get('receiver_id', 'openimis'),
                'receiver_id': request_data.get('header', {}).get('sender_id', 'unknown'),
                'is_msg_encrypted': False,
            },
            'message': {
                'transaction_id': request_data.get('message', {}).get('transaction_id', ''),
                'status': 'error',
                'error_message': error_message,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        }
