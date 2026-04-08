"""
DCI Notify ViewSet

REST API view for receiving SPDCI notify callbacks.
This endpoint is called BY other registries when WE are a subscriber.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
import logging

from ..serializers import (
    DCINotifyRequestSerializer,
    DCINotifyResponseSerializer,
)
from ..permissions import DCIPersonPermissions

logger = logging.getLogger(__name__)


@extend_schema(
    tags=['DCI Registry'],
    summary='Receive registry event notifications',
    description='''
    Receive notifications from other registries when subscribed to their events.

    **SPDCI FR/SR/IBR Compliant - Callback Receiver**

    This endpoint is called BY external registries to notify us about:
    - REGISTER: New person/farmer/member registered
    - UPDATE: Existing record updated
    - DEREGISTER: Record deactivated/deleted

    When we subscribe to another registry (providing our sender_uri),
    that registry will POST notify requests to this endpoint.

    The notification contains the full resource record in SPDCI format.
    ''',
    request=DCINotifyRequestSerializer,
    responses={
        200: DCINotifyResponseSerializer,
    }
)
@api_view(['POST'])
@permission_classes([DCIPersonPermissions])
def notify(request):
    """
    DCI notify callback receiver endpoint.

    POST /api/api_dci/registry/notify

    Receives event notifications from external registries when we are a subscriber.
    Returns ACK to confirm receipt.
    """
    logger.info("[DCI Notify] Received notification from external registry")

    # Validate request
    serializer = DCINotifyRequestSerializer(data=request.data)
    if not serializer.is_valid():
        logger.error(f"[DCI Notify] Validation errors: {serializer.errors}")
        return Response(
            {
                'header': {
                    'status': 'error',
                    'message': 'Invalid notify request format'
                },
                'errors': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    validated_data = serializer.validated_data

    try:
        header_data = validated_data['header']
        message_data = validated_data['message']
        transaction_id = message_data['transaction_id']
        notify_requests = message_data.get('notify_request', [])

        sender_id = header_data.get('sender_id')

        logger.info(
            f"[DCI Notify] Processing {len(notify_requests)} notifications "
            f"from {sender_id}, transaction {transaction_id}"
        )

        # Process each notification
        for notify_item in notify_requests:
            reference_id = notify_item.get('reference_id', '')
            subscription_id = notify_item.get('subscription_id', '')
            data = notify_item.get('data', {})

            event_type = data.get('event_type', 'UNKNOWN')
            reg_record_type = data.get('reg_record_type', 'Unknown')
            reg_record = data.get('reg_record', {})

            logger.info(
                f"[DCI Notify] Received {event_type} event for {reg_record_type} "
                f"(subscription {subscription_id}, ref {reference_id})"
            )

            # TODO: Process the notification
            # Options:
            # 1. Store in a notification queue for async processing
            # 2. Update local database if we maintain a cache
            # 3. Trigger business logic based on event type
            # 4. Log to audit table

            # For now, just log it
            logger.debug(f"[DCI Notify] Event data: {reg_record}")

        # Build ACK response (SPDCI FR format)
        response_data = DCINotifyResponseSerializer.create_ack_response(
            request_data=request.data,
            transaction_id=transaction_id
        )

        logger.info(
            f"[DCI Notify] Successfully processed {len(notify_requests)} notifications "
            f"for transaction {transaction_id}, returning ACK"
        )

        return Response(response_data, status=status.HTTP_200_OK)

    except KeyError as e:
        logger.error(f"[DCI Notify] Missing required field: {e}")
        return Response(
            {
                'header': {
                    'status': 'error',
                    'message': f'Missing required field: {e}'
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"[DCI Notify] Unexpected error: {e}", exc_info=True)
        return Response(
            {
                'header': {
                    'status': 'error',
                    'message': f'Internal server error: {str(e)}'
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
