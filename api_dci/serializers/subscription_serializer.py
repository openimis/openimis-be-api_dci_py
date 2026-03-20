"""
DCI Subscription Serializers

Serializers for SPDCI subscribe, unsubscribe, and notify operations.
"""
from rest_framework import serializers
from datetime import datetime


class DCISubscribeRequestItemSerializer(serializers.Serializer):
    """Individual subscribe request item"""
    reference_id = serializers.CharField(max_length=255)
    timestamp = serializers.DateTimeField()
    filter = serializers.DictField(required=False, help_text="SPDCI query filter")
    event_type = serializers.CharField(max_length=50, required=False, default="ALL")
    expiry = serializers.DateTimeField(required=False, allow_null=True)
    locale = serializers.CharField(max_length=50, required=False)


class DCISubscribeMessageSerializer(serializers.Serializer):
    """DCI subscribe request message - SPDCI FR format"""
    transaction_id = serializers.CharField(max_length=255)
    subscribe_request = DCISubscribeRequestItemSerializer(many=True)


class DCISubscribeRequestSerializer(serializers.Serializer):
    """
    Complete DCI subscribe request
    POST /api/api_dci/registry/subscribe
    """
    signature = serializers.JSONField(required=False, allow_null=True)
    header = serializers.DictField()  # Reuse DCIHeaderSerializer
    message = DCISubscribeMessageSerializer()


class DCIUnsubscribeRequestItemSerializer(serializers.Serializer):
    """Individual unsubscribe request item"""
    reference_id = serializers.CharField(max_length=255)
    timestamp = serializers.DateTimeField()
    subscription_id = serializers.CharField(
        max_length=255,
        help_text="Subscription code to unsubscribe"
    )
    locale = serializers.CharField(max_length=50, required=False)


class DCIUnsubscribeMessageSerializer(serializers.Serializer):
    """DCI unsubscribe request message"""
    transaction_id = serializers.CharField(max_length=255)
    unsubscribe_request = DCIUnsubscribeRequestItemSerializer(many=True, required=False)


class DCIUnsubscribeRequestSerializer(serializers.Serializer):
    """
    Complete DCI unsubscribe request
    POST /api/api_dci/registry/unsubscribe
    """
    signature = serializers.JSONField(required=False, allow_null=True)
    header = serializers.DictField()
    message = DCIUnsubscribeMessageSerializer()


class DCINotifyDataSerializer(serializers.Serializer):
    """Notification data payload"""
    version = serializers.CharField(default="1.0.0")
    reg_type = serializers.CharField()
    reg_record_type = serializers.CharField()
    event_type = serializers.CharField()
    reg_record = serializers.DictField(help_text="The changed Person/Farmer/Member record")


class DCINotifyRequestItemSerializer(serializers.Serializer):
    """Individual notify request item"""
    reference_id = serializers.CharField(max_length=255)
    timestamp = serializers.DateTimeField()
    subscription_id = serializers.CharField(max_length=255)
    data = DCINotifyDataSerializer()
    locale = serializers.CharField(max_length=50, required=False)


class DCINotifyMessageSerializer(serializers.Serializer):
    """DCI notify request message (sent FROM registry TO subscriber)"""
    transaction_id = serializers.CharField(max_length=255)
    correlation_id = serializers.CharField(max_length=255, required=False)
    notify_request = DCINotifyRequestItemSerializer(many=True, required=False)


class DCINotifyRequestSerializer(serializers.Serializer):
    """
    Complete DCI notify request (callback to subscriber)
    POST {subscriber.sender_uri}
    """
    signature = serializers.JSONField(required=False, allow_null=True)
    header = serializers.DictField()
    message = DCINotifyMessageSerializer()


# Response serializers

class DCISubscribeResponseSerializer(serializers.Serializer):
    """Subscribe response serializer - Returns ACK response per SPDCI FR spec"""

    @classmethod
    def create_ack_response(cls, request_data, transaction_id):
        """
        Create a DCI subscribe ACK response

        Args:
            request_data: Original request data dict
            transaction_id: Transaction ID from request

        Returns:
            dict: DCI ACK response formatted per SPDCI FR spec
        """
        return {
            'signature': request_data.get('signature', ""),
            'header': {
                'version': '1.0.0',
                'message_id': f"ack-{request_data['header']['message_id']}",
                'message_ts': datetime.utcnow().isoformat() + 'Z',
                'action': 'on-subscribe',
                'status': 'succ',
                'sender_id': request_data['header'].get('receiver_id', 'openimis'),
                'receiver_id': request_data['header']['sender_id'],
                'is_msg_encrypted': request_data['header'].get('is_msg_encrypted', False),
            },
            'message': {
                'ack_status': 'ACK',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'correlation_id': transaction_id,
            }
        }


class DCINotifyResponseSerializer(serializers.Serializer):
    """Notify callback response serializer - Returns ACK per SPDCI FR spec"""

    @classmethod
    def create_ack_response(cls, request_data, transaction_id):
        """
        Create a DCI notify ACK response

        Args:
            request_data: Original notify request data dict
            transaction_id: Transaction ID from request

        Returns:
            dict: DCI ACK response formatted per SPDCI FR spec
        """
        message = {
            'ack_status': 'ACK',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'correlation_id': transaction_id,
        }

        # Only include error field if there's an error (omit when successful)
        # This matches SPDCI OpenAPI schema expectations

        return {
            'signature': request_data.get('signature', ""),
            'header': {
                'version': '1.0.0',
                'message_id': f"ack-{request_data['header']['message_id']}",
                'message_ts': datetime.utcnow().isoformat() + 'Z',
                'action': 'on-notify',
                'status': 'succ',
                'sender_id': request_data['header'].get('receiver_id', 'openimis'),
                'receiver_id': request_data['header']['sender_id'],
                'is_msg_encrypted': request_data['header'].get('is_msg_encrypted', False),
            },
            'message': message
        }


class DCIUnsubscribeResponseSerializer(serializers.Serializer):
    """Unsubscribe response serializer - Returns ACK response per SPDCI FR spec"""

    @classmethod
    def create_ack_response(cls, request_data, transaction_id):
        """
        Create a DCI unsubscribe ACK response

        Args:
            request_data: Original request data dict
            transaction_id: Transaction ID from request

        Returns:
            dict: DCI ACK response formatted per SPDCI FR spec
        """
        return {
            'signature': request_data.get('signature', ""),
            'header': {
                'version': '1.0.0',
                'message_id': f"ack-{request_data['header']['message_id']}",
                'message_ts': datetime.utcnow().isoformat() + 'Z',
                'action': 'on-unsubscribe',
                'status': 'succ',
                'sender_id': request_data['header'].get('receiver_id', 'openimis'),
                'receiver_id': request_data['header']['sender_id'],
                'is_msg_encrypted': request_data['header'].get('is_msg_encrypted', False),
            },
            'message': {
                'ack_status': 'ACK',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'correlation_id': transaction_id,
            }
        }

    @classmethod
    def create_response(cls, request_data, unsubscribe_results, transaction_id):
        """
        Create a DCI unsubscribe response (kept for potential async callback use)

        Args:
            request_data: Original request data dict
            unsubscribe_results: List of (reference_id, success, message) tuples
            transaction_id: Transaction ID from request

        Returns:
            dict: DCI response formatted per SPDCI FR spec
        """
        # Build unsubscribe_response array
        unsubscribe_responses = []
        for ref_id, success, message in unsubscribe_results:
            unsubscribe_responses.append({
                "reference_id": ref_id,
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "status": "succ" if success else "fail",
                "status_reason_message": message
            })

        return {
            'signature': request_data.get('signature', ""),
            'header': {
                'version': '1.0.0',
                'message_id': f"response-{request_data['header']['message_id']}",
                'message_ts': datetime.utcnow().isoformat() + 'Z',
                'action': 'on-unsubscribe',
                'status': 'succ',
                'sender_id': request_data['header'].get('receiver_id', 'openimis'),
                'receiver_id': request_data['header']['sender_id'],
                'total_count': len(unsubscribe_results),
                'is_msg_encrypted': False,
                'meta': {}
            },
            'message': {
                'transaction_id': transaction_id,
                'correlation_id': transaction_id,
                'unsubscribe_response': unsubscribe_responses
            }
        }
