"""
DCI Callback Receiver ViewSet

REST API views for receiving SPDCI async callbacks:
- on-search      : result of an async search
- on-subscribe   : result of a subscribe request
- on-unsubscribe : result of an unsubscribe request
- txn/on-status  : result of a txn status request
"""
from datetime import datetime
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
import logging

from ..permissions import DCIPersonPermissions

logger = logging.getLogger(__name__)


def _ack_response(request_data, action):
    """Build a standard ACK response for any callback endpoint."""
    header = request_data.get('header', {})
    return {
        'signature': request_data.get('signature', ''),
        'header': {
            'version': '1.0.0',
            'message_id': f"ack-{header.get('message_id', '')}",
            'message_ts': datetime.utcnow().isoformat() + 'Z',
            'action': action,
            'status': 'succ',
            'sender_id': header.get('receiver_id', 'openimis'),
            'receiver_id': header.get('sender_id', ''),
            'is_msg_encrypted': header.get('is_msg_encrypted', False),
        },
        'message': {
            'ack_status': 'ACK',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'correlation_id': request_data.get('message', {}).get('transaction_id', ''),
        },
    }


def _callback_view(request, endpoint_label, ack_action):
    """Generic handler for all callback receiver endpoints."""
    if 'header' not in request.data:
        return Response(
            {'header': {'status': 'error', 'message': 'Missing header'}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    logger.info(f"[DCI {endpoint_label}] Received callback from {request.user}")
    return Response(_ack_response(request.data, ack_action), status=status.HTTP_200_OK)


@extend_schema(
    tags=['DCI Registry'],
    summary='Receive on-search callback',
    description='Receives async search results posted back by an external registry.',
)
@api_view(['POST'])
@permission_classes([DCIPersonPermissions])
def on_search(request):
    """POST /api/api_dci/registry/on-search"""
    return _callback_view(request, 'OnSearch', 'on-search')


@extend_schema(
    tags=['DCI Registry'],
    summary='Receive on-subscribe callback',
    description='Receives subscribe confirmation posted back by an external registry.',
)
@api_view(['POST'])
@permission_classes([DCIPersonPermissions])
def on_subscribe(request):
    """POST /api/api_dci/registry/on-subscribe"""
    return _callback_view(request, 'OnSubscribe', 'on-subscribe')


@extend_schema(
    tags=['DCI Registry'],
    summary='Receive on-unsubscribe callback',
    description='Receives unsubscribe confirmation posted back by an external registry.',
)
@api_view(['POST'])
@permission_classes([DCIPersonPermissions])
def on_unsubscribe(request):
    """POST /api/api_dci/registry/on-unsubscribe"""
    return _callback_view(request, 'OnUnsubscribe', 'on-unsubscribe')


@extend_schema(
    tags=['DCI Registry'],
    summary='Receive txn on-status callback',
    description='Receives transaction status results posted back by an external registry.',
)
@api_view(['POST'])
@permission_classes([DCIPersonPermissions])
def txn_on_status(request):
    """POST /api/api_dci/registry/txn/on-status"""
    return _callback_view(request, 'TxnOnStatus', 'on-txn-status')
