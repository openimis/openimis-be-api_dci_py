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
    reg_type = serializers.CharField(max_length=50)
    query_type = serializers.CharField(max_length=50)
    query = DCIPersonSerializer()


class DCISearchMessageSerializer(serializers.Serializer):
    """DCI search request message"""
    transaction_id = serializers.CharField(max_length=255)
    search_criteria = DCISearchCriteriaSerializer()


class DCISearchRequestSerializer(serializers.Serializer):
    """
    Complete DCI search request
    POST /api/dci/reg/sync/search
    """
    signature = DCISignatureSerializer(required=False)
    header = DCIHeaderSerializer()
    message = DCISearchMessageSerializer()


class DCISearchResponseMessageSerializer(serializers.Serializer):
    """DCI search response message"""
    transaction_id = serializers.CharField(max_length=255)
    data = DCIPersonSerializer(many=True)
    count = serializers.IntegerField()


class DCISearchResponseSerializer(serializers.Serializer):
    """
    Complete DCI search response
    Response for POST /api/dci/reg/sync/search
    """
    signature = DCISignatureSerializer(required=False)
    header = DCIHeaderSerializer()
    message = DCISearchResponseMessageSerializer()
    
    @classmethod
    def create_response(cls, request_data, persons, transaction_id):
        """
        Create a DCI search response from request and results
        
        Args:
            request_data: Original request data dict
            persons: List of DCI Person dicts
            transaction_id: Transaction ID from request
            
        Returns:
            dict: DCI response data
        """
        return {
            'signature': request_data.get('signature', {}),
            'header': {
                'version': '1.0.0',
                'message_id': f"response-{request_data['header']['message_id']}",
                'message_ts': datetime.utcnow().isoformat() + 'Z',
                'action': 'on-search',
                'sender_id': request_data['header'].get('receiver_id', 'openimis'),
                'receiver_id': request_data['header']['sender_id'],
                'status': 'success'
            },
            'message': {
                'transaction_id': transaction_id,
                'data': persons,
                'count': len(persons)
            }
        }