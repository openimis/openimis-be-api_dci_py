"""
DCI Person Serializers

Serializers for DCI standard message format.
"""
from rest_framework import serializers
from datetime import datetime


class DCISignatureSerializer(serializers.Serializer):
    """DCI message signature"""
    created = serializers.DateTimeField(required=False)
    expires = serializers.DateTimeField(required=False)


class DCIHeaderSerializer(serializers.Serializer):
    """DCI message header"""
    version = serializers.CharField(max_length=10, default="1.0.0")
    message_id = serializers.CharField(max_length=255)
    message_ts = serializers.DateTimeField()
    action = serializers.CharField(max_length=50)
    sender_id = serializers.CharField(max_length=255)
    receiver_id = serializers.CharField(max_length=255, required=False)
    status = serializers.CharField(max_length=50, required=False)


class DCIPersonSerializer(serializers.Serializer):
    """
    DCI Person object serializer
    Based on: https://schema.spdci.org/core/v1/data/Person.jsonld
    """
    type = serializers.CharField(source='@type', default='Person', read_only=True)
    id = serializers.CharField(required=False)
    firstName = serializers.CharField(max_length=255, required=False)
    lastName = serializers.CharField(max_length=255, required=False)
    dob = serializers.DateField(required=False)
    gender = serializers.CharField(max_length=50, required=False)
    phone = serializers.CharField(max_length=50, required=False)
    email = serializers.EmailField(required=False)


class DCISearchCriteriaSerializer(serializers.Serializer):
    """DCI search criteria"""
    reg_type = serializers.CharField(max_length=50, required=False)
    query_type = serializers.CharField(max_length=50)
    query = serializers.JSONField()  # Can be Person object or expression/predicate


class DCISearchRequestItemSerializer(serializers.Serializer):
    """FR-style search request item"""
    reference_id = serializers.CharField(max_length=255)
    timestamp = serializers.DateTimeField()
    search_criteria = DCISearchCriteriaSerializer()
    pagination = serializers.JSONField(required=False)
    locale = serializers.CharField(max_length=10, required=False)


class DCISearchMessageSerializer(serializers.Serializer):
    """DCI search request message - supports both IBR and FR formats"""
    transaction_id = serializers.CharField(max_length=255)
    # IBR format: direct search_criteria
    search_criteria = DCISearchCriteriaSerializer(required=False)
    # FR format: array of search_request items
    search_request = DCISearchRequestItemSerializer(many=True, required=False)


class DCISearchRequestSerializer(serializers.Serializer):
    """
    Complete DCI search request
    POST /api/dci/reg/sync/search
    """
    signature = serializers.JSONField(required=False)  # Can be string or object
    header = DCIHeaderSerializer()
    message = DCISearchMessageSerializer()


class DCISearchResponseMessageSerializer(serializers.Serializer):
    """DCI search response message"""
    transaction_id = serializers.CharField(max_length=255)
    data = DCIPersonSerializer(many=True, required=False)  # IBR format
    count = serializers.IntegerField(required=False)  # IBR format
    search_response = serializers.JSONField(required=False)  # FR format
    correlation_id = serializers.CharField(max_length=255, required=False)  # FR format


class DCISearchResponseSerializer(serializers.Serializer):
    """
    Complete DCI search response
    Response for POST /api/dci/reg/sync/search
    """
    signature = DCISignatureSerializer(required=False)
    header = DCIHeaderSerializer()
    message = DCISearchResponseMessageSerializer()

    @classmethod
    def create_response(cls, request_data, persons, transaction_id, format_type='ibr'):
        """
        Create a DCI search response from request and results

        Args:
            request_data: Original request data dict
            persons: List of DCI Person dicts
            transaction_id: Transaction ID from request
            format_type: 'ibr' or 'fr' - determines response format

        Returns:
            dict: DCI response data
        """
        message = request_data.get('message', {})

        # Determine format based on request structure if not explicitly set
        if format_type == 'auto':
            format_type = 'fr' if 'search_request' in message else 'ibr'

        header = {
            'version': '1.0.0',
            'message_id': f"response-{request_data['header']['message_id']}",
            'message_ts': datetime.utcnow().isoformat() + 'Z',
            'action': 'on-search',
            'sender_id': request_data['header'].get('receiver_id', 'openimis-server'),
            'receiver_id': request_data['header']['sender_id'],
            'status': 'succ',  # FR standard uses 'succ' not 'success'
            'total_count': 1,
            'completed_count': 1
        }

        if format_type == 'fr':
            # FR format with search_response array
            search_request = message.get('search_request', [{}])[0]
            reference_id = search_request.get('reference_id', f"ref-{transaction_id}")

            return {
                'signature': request_data.get('signature', 'unsigned'),
                'header': header,
                'message': {
                    'transaction_id': transaction_id,
                    'correlation_id': transaction_id,
                    'search_response': [{
                        'reference_id': reference_id,
                        'timestamp': datetime.utcnow().isoformat() + 'Z',
                        'status': 'succ',
                        'data': {
                            'version': '1.0.0',
                            'reg_record_type': 'Farmer',  # FR standard
                            'reg_records': persons
                        }
                    }]
                }
            }
        else:
            # IBR format with direct data array
            return {
                'signature': request_data.get('signature', 'unsigned'),
                'header': header,
                'message': {
                    'transaction_id': transaction_id,
                    'data': persons,
                    'count': len(persons)
                }
            }
