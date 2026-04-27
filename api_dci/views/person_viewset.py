"""
DCI Person ViewSet

REST API views for DCI Registry search operations.

Endpoints:
  - POST /reg/sync/search   → Synchronous: returns full results inline (HTTP 200)
  - POST /reg/search         → Asynchronous: returns ACK (HTTP 202), processes in
                               background, POSTs results to sender_uri callback.
                               Results also stored for polling via /reg/txn/status.
  - POST /reg/txn/status     → Poll for async search results by transaction_id.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiExample

from ..serializers import (
    DCISearchRequestSerializer,
    DCISearchResponseSerializer,
)
from ..converters.person_converter import PersonConverter
from ..permissions import DCIPersonPermissions

# In-memory store for async search results (keyed by transaction_id)
# In production this would be Redis/DB, but for now this works.
_async_results_store = {}


def _build_queryset_from_search(search_request):
    """
    Parse a single DCI search_request item and return a filtered
    Individual queryset.
    """
    from individual.models import Individual

    search_criteria = search_request.get('search_criteria', {})
    query_obj = search_criteria.get('query', {})

    # Navigate DCI expression structure: query -> value -> expression -> query
    expression_q = query_obj.get('value', {}).get('expression', {}).get('query', {})

    # fallback to the flat query if expression structure is missing
    if not expression_q:
        expression_q = query_obj

    queryset = Individual.objects.filter(is_deleted=False)

    # Find $and arrays or treat as flat dict
    filter_list = expression_q.get('$and', [])
    if not filter_list and isinstance(expression_q, dict) and '$and' not in expression_q:
        filter_list = [{k: {"$eq": v}} for k, v in expression_q.items() if k != '@type']

    # Extract filters
    filters = {}
    for item in filter_list:
        if isinstance(item, dict):
            for k, v in item.items():
                if isinstance(v, dict) and '$eq' in v:
                    filters[k] = v['$eq']
                else:
                    filters[k] = v

    # Apply search filters
    if 'firstName' in filters:
        queryset = queryset.filter(first_name__icontains=filters['firstName'])
    if 'lastName' in filters:
        queryset = queryset.filter(last_name__icontains=filters['lastName'])
    if 'dob' in filters:
        queryset = queryset.filter(dob=filters['dob'])
    if 'gender' in filters:
        # Individual model has no direct gender field; sex is stored in json_ext
        # json_ext examples: {"sex": "male"} or {"sex": "M"} depending on data source
        gender_val = filters['gender'].lower()   # "male" / "female" / "other"
        gender_code = {'male': 'M', 'female': 'F', 'other': 'O'}.get(gender_val, gender_val[0].upper() if gender_val else None)
        from django.db.models import Q
        if gender_code:
            queryset = queryset.filter(
                Q(json_ext__sex__iexact=gender_val) |
                Q(json_ext__sex__iexact=gender_code)
            )
    if 'phone' in filters:
        queryset = queryset.filter(json_ext__phone__icontains=filters['phone'])
    if 'email' in filters:
        queryset = queryset.filter(json_ext__email__icontains=filters['email'])

    # Pagination
    pagination = search_criteria.get('pagination', {})
    page_size = min(pagination.get('page_size', 100), 500)
    page_number = max(pagination.get('page_number', 1), 1)
    offset = (page_number - 1) * page_size

    return queryset, offset, page_size


def _convert_to_persons(queryset, offset, page_size, registry_type=None):
    """Convert queryset slice to SPDCI-compliant registry records."""
    if registry_type is None:
        from ..apps import ApiDciConfig
        registry_type = ApiDciConfig.registry_type

    return [
        PersonConverter.individual_to_dci_person(individual, registry_type=registry_type)
        for individual in queryset[offset:offset + page_size]
    ]


# ═══════════════════════════════════════════════════════════════════════
#  SYNC SEARCH — returns full results inline (HTTP 200)
# ═══════════════════════════════════════════════════════════════════════

@extend_schema(
    tags=['DCI Registry'],
    summary='Sync Search for Person records',
    description='''
    Synchronously search for Person records following the DCI standard.
    Returns full results immediately in the response body (HTTP 200).
    ''',
    request=DCISearchRequestSerializer,
    responses={200: DCISearchResponseSerializer},
)
@api_view(['POST'])
@permission_classes([DCIPersonPermissions])
def sync_search(request):
    """
    DCI sync/search endpoint.
    POST /api/dci/reg/sync/search

    Returns full SPDCI-compliant results immediately.
    """
    serializer = DCISearchRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                'header': {'status': 'error', 'message': 'Invalid request format'},
                'errors': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    validated_data = serializer.validated_data

    try:
        message_data = validated_data['message']
        transaction_id = message_data['transaction_id']
        search_requests = message_data.get('search_request', [])

        if not search_requests:
            raise ValueError("No search_request provided")

        search_request = search_requests[0]
        reference_id = search_request.get('reference_id', '')

        queryset, offset, page_size = _build_queryset_from_search(search_request)

        from ..apps import ApiDciConfig
        registry_type = ApiDciConfig.registry_type
        persons = _convert_to_persons(queryset, offset, page_size, registry_type)

    except ImportError:
        return Response(
            {'header': {'status': 'error', 'message': 'Individual module not available'}},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except Exception as e:
        return Response(
            {'header': {'status': 'error', 'message': str(e)}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    response_data = DCISearchResponseSerializer.create_response(
        request_data=request.data,
        persons=persons,
        transaction_id=transaction_id,
        reference_id=reference_id
    )

    return Response(response_data, status=status.HTTP_200_OK)


# ═══════════════════════════════════════════════════════════════════════
#  ASYNC SEARCH — returns ACK (HTTP 202), processes in background,
#  POSTs to sender_uri AND stores results for txn/status polling.
# ═══════════════════════════════════════════════════════════════════════

@extend_schema(
    tags=['DCI Registry'],
    summary='Async Search for Person records',
    description='''
    Asynchronously search for Person records following the DCI standard.

    Returns an immediate 202 ACK response. The server processes the search
    in the background and:
      1. POSTs full results to the sender_uri callback (if provided).
      2. Stores results for polling via POST /reg/txn/status.
    ''',
    request=DCISearchRequestSerializer,
    responses={202: DCISearchResponseSerializer},
)
@api_view(['POST'])
@permission_classes([DCIPersonPermissions])
def async_search(request):
    """
    DCI async search endpoint.
    POST /api/dci/reg/search

    Returns HTTP 202 ACK immediately.
    Background thread processes the query, stores results, and optionally
    POSTs them to sender_uri.
    """
    serializer = DCISearchRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                'header': {'status': 'error', 'message': 'Invalid request format'},
                'errors': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    validated_data = serializer.validated_data

    try:
        message_data = validated_data['message']
        transaction_id = message_data['transaction_id']
        search_requests = message_data.get('search_request', [])

        if not search_requests:
            raise ValueError("No search_request provided")

        # Mark as pending
        _async_results_store[transaction_id] = {
            'status': 'pdng',
            'result': None,
        }

        # Queue background processing
        from ..tasks import BackgroundSearchTask
        task = BackgroundSearchTask(
            request_data=request.data,
            search_requests=search_requests,
            results_store=_async_results_store,
        )
        task.start()

    except Exception as e:
        return Response(
            {'header': {'status': 'error', 'message': str(e)}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Return immediate ACK (HTTP 202) — no data yet
    response_data = DCISearchResponseSerializer.create_ack_response(
        request_data=request.data,
        transaction_id=transaction_id
    )

    return Response(response_data, status=status.HTTP_202_ACCEPTED)


# ═══════════════════════════════════════════════════════════════════════
#  TXN STATUS — poll for async search results
# ═══════════════════════════════════════════════════════════════════════

@extend_schema(
    tags=['DCI Registry'],
    summary='Check async transaction status',
    description='''
    Poll for the status/results of an async search by transaction_id.

    Returns:
      - status "pdng" if still processing
      - status "succ" with full search results when complete
      - status "rjct" if the search failed
    ''',
)
@api_view(['POST'])
@permission_classes([DCIPersonPermissions])
def txn_status(request):
    """
    DCI transaction status endpoint.
    POST /api/dci/reg/txn/status

    Request:
    {
        "header": { ... },
        "message": {
            "transaction_id": "txn-async-all-001",
            "txnstatus_request": {
                "txn_type": "search",
                "attribute_type": "transaction_id",
                "attribute_value": "txn-async-all-001"
            }
        }
    }
    """
    try:
        message = request.data.get('message', {})
        txn_request = message.get('txnstatus_request', {})

        # Support both flat transaction_id and nested attribute_value
        transaction_id = txn_request.get('attribute_value') or message.get('transaction_id', '')

        if not transaction_id:
            return Response(
                {'header': {'status': 'error', 'message': 'transaction_id is required'}},
                status=status.HTTP_400_BAD_REQUEST
            )

        stored = _async_results_store.get(transaction_id)

        if stored is None:
            return Response(
                {
                    'header': {'status': 'error', 'message': f'Transaction {transaction_id} not found'},
                    'message': {
                        'transaction_id': transaction_id,
                        'txnstatus_response': {
                            'txn_type': 'search',
                            'txn_status': 'not_found',
                        }
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if stored['status'] == 'pdng':
            return Response(
                {
                    'header': {'status': 'pdng', 'message': 'Search is still processing'},
                    'message': {
                        'transaction_id': transaction_id,
                        'txnstatus_response': {
                            'txn_type': 'search',
                            'txn_status': 'pdng',
                        }
                    }
                },
                status=status.HTTP_200_OK
            )

        if stored['status'] == 'succ':
            return Response(stored['result'], status=status.HTTP_200_OK)

        # rjct / error
        return Response(
            {
                'header': {'status': 'rjct', 'message': stored.get('error', 'Search failed')},
                'message': {
                    'transaction_id': transaction_id,
                    'txnstatus_response': {
                        'txn_type': 'search',
                        'txn_status': 'rjct',
                    }
                }
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response(
            {'header': {'status': 'error', 'message': str(e)}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
