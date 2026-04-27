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
    sender_uri = serializers.CharField(max_length=255, required=False, allow_blank=True)
    receiver_id = serializers.CharField(max_length=255, required=False)
    total_count = serializers.IntegerField(required=False)
    is_msg_encrypted = serializers.BooleanField(default=False, required=False)
    meta = serializers.DictField(required=False)
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
    version = serializers.CharField(max_length=50, required=False)
    reg_type = serializers.CharField(max_length=100)
    reg_record_type = serializers.CharField(max_length=255, required=False)
    query_type = serializers.CharField(max_length=50)
    query = serializers.DictField()
    sort = serializers.ListField(child=serializers.DictField(), required=False)
    pagination = serializers.DictField(required=False)
    consent = serializers.DictField(required=False)
    authorize = serializers.DictField(required=False)


class DCISearchRequestItemSerializer(serializers.Serializer):
    reference_id = serializers.CharField(max_length=255)
    timestamp = serializers.DateTimeField()
    search_criteria = DCISearchCriteriaSerializer()
    locale = serializers.CharField(max_length=50, required=False)


class DCISearchMessageSerializer(serializers.Serializer):
    """DCI search request message"""
    transaction_id = serializers.CharField(max_length=255)
    search_request = DCISearchRequestItemSerializer(many=True)


class DCISearchRequestSerializer(serializers.Serializer):
    """
    Complete DCI search request
    POST /api/dci/reg/sync/search
    """
    signature = serializers.CharField(required=False, allow_blank=True)
    header = DCIHeaderSerializer()
    message = DCISearchMessageSerializer()


class DCISearchResponseMessageSerializer(serializers.Serializer):
    """DCI search response message"""
    transaction_id = serializers.CharField(max_length=255)
    search_response = serializers.ListField(child=serializers.DictField())


class DCISearchResponseSerializer(serializers.Serializer):
    """
    Complete DCI search response
    Response for POST /api/dci/reg/sync/search
    """
    signature = serializers.CharField(required=False, allow_blank=True)
    header = DCIHeaderSerializer()
    message = DCISearchResponseMessageSerializer()
    
    @classmethod
    def create_response(cls, request_data, persons, transaction_id,
                        reference_id="", registry_type=None):
        """
        Create a SPDCI-compliant search response.

        Args:
            request_data: Original request data dict
            persons: List of SPDCI reg_record dicts (Group or Farmer)
            transaction_id: Transaction ID from request
            reference_id: Reference ID to tie response to request
            registry_type: "social" or "farmer" (falls back to app config)

        Returns:
            dict: SPDCI response data
        """
        if registry_type is None:
            from ..apps import ApiDciConfig
            registry_type = ApiDciConfig.registry_type

        if registry_type == "farmer":
            reg_type = "ns:org:RegistryType:FR"
            reg_record_type = "spdci-extensions-dci:Farmer"
        else:
            reg_type = "ns:org:RegistryType:Social"
            reg_record_type = "Group"

        search_criteria = {}
        search_reqs = request_data.get('message', {}).get('search_request', [])
        if search_reqs:
            search_criteria = search_reqs[0].get('search_criteria', {})

        pagination = search_criteria.get('pagination', {})
        page_size = pagination.get('page_size', 100)
        page_number = pagination.get('page_number', 1)

        return {
            'signature': request_data.get('signature', ""),
            'header': {
                'version': '1.0.0',
                'message_id': f"response-{request_data['header']['message_id']}",
                'message_ts': datetime.utcnow().isoformat() + 'Z',
                'action': 'on-search',
                'sender_id': request_data['header'].get('receiver_id', 'openimis'),
                'sender_uri': request_data['header'].get('sender_uri', ''),
                'receiver_id': request_data['header']['sender_id'],
                'total_count': len(persons),
                'is_msg_encrypted': request_data['header'].get('is_msg_encrypted', False),
                'meta': request_data['header'].get('meta', {}),
                'status': 'succ',
                'status_reason_code': '',
                'status_reason_message': 'Success',
                'completed_count': len(persons),
            },
            'message': {
                'transaction_id': transaction_id,
                'correlation_id': f"corr-{transaction_id}",
                'search_response': [
                    {
                        "reference_id": reference_id,
                        "timestamp": datetime.utcnow().isoformat() + 'Z',
                        "status": "succ",
                        "status_reason_code": "",
                        "status_reason_message": "Success",
                        "data": {
                            "version": "1.0.0",
                            "reg_type": reg_type,
                            "reg_record_type": reg_record_type,
                            "reg_records": persons,
                        },
                        "pagination": {
                            "page_size": page_size,
                            "page_number": page_number,
                            "total_count": len(persons),
                        },
                        "locale": "eng",
                    }
                ]
            }
        }
    
    @classmethod
    def create_ack_response(cls, request_data, transaction_id):
        """
        Create a DCI async search acknowledgment response.
        Should be returned immediately (HTTP 202) queueing the request.
        """
        return {
            'signature': request_data.get('signature', ""),
            'header': {
                'version': '1.0.0',
                'message_id': f"ack-{request_data['header']['message_id']}",
                'message_ts': datetime.utcnow().isoformat() + 'Z',
                'action': 'on-search',
                'sender_id': request_data['header'].get('receiver_id', 'openimis'),
                'sender_uri': request_data['header'].get('sender_uri', ''),
                'receiver_id': request_data['header']['sender_id'],
                'is_msg_encrypted': False,
                'status': 'success'
            },
            'message': {
                'transaction_id': transaction_id,
                'search_response': []
            }
        }