"""
DCI Person ViewSet

REST API views for DCI Person sync/search operations.
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


@extend_schema(
    tags=['DCI Registry'],
    summary='Search for Person records',
    description='''
    Search for Person records following the DCI (Digital Convergence Initiative) standard.

    This endpoint implements the DCI Registry Core API specification for searching Person records.
    The request and response follow the DCI message format with signature, header, and message sections.
    ''',
    request=DCISearchRequestSerializer,
    responses={
        200: DCISearchResponseSerializer,
    }
)
@api_view(['POST'])
@permission_classes([DCIPersonPermissions])
def sync_search(request):
    """
    DCI sync/search endpoint for Person records.
    
    POST /api/dci/reg/sync/search
    
    This endpoint implements the DCI Registry Core API specification
    for searching Person records.
    
    Request body follows DCI message format:
    {
        "signature": {...},
        "header": {...},
        "message": {
            "transaction_id": "...",
            "search_criteria": {
                "reg_type": "person",
                "query_type": "sync",
                "query": {
                    "@type": "Person",
                    "firstName": "John",
                    "lastName": "Doe"
                }
            }
        }
    }
    
    Response follows DCI message format with matching Person records.
    """
    # Validate request
    serializer = DCISearchRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                'header': {
                    'status': 'error',
                    'message': 'Invalid request format'
                },
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
        search_criteria = search_request.get('search_criteria', {})
        query_obj = search_criteria.get('query', {})
        
        # Navigate DCI expression structure: query -> value -> expression -> query
        expression_q = query_obj.get('value', {}).get('expression', {}).get('query', {})
        
        # fallback to the flat query if expression structure is missing (for backward compatibility if needed)
        if not expression_q:
            expression_q = query_obj

        # Build query for Individual model
        from individual.models import Individual

        # Start with all valid individuals
        queryset = Individual.objects.filter(is_deleted=False)
        
        # Find $and or $or arrays if they exist, or just use expression_q as a flat dict
        filter_list = expression_q.get('$and', [])
        if not filter_list and isinstance(expression_q, dict) and '$and' not in expression_q:
            # Maybe flat
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
            # Map DCI gender to OpenIMIS gender code
            gender_map = {
                'Male': 'M',
                'Female': 'F',
                'Other': 'O'
            }
            gender_code = gender_map.get(filters['gender'])
            if gender_code:
                queryset = queryset.filter(gender__code=gender_code)
        
        if 'phone' in filters:
            queryset = queryset.filter(phone__icontains=filters['phone'])
        
        if 'email' in filters:
            queryset = queryset.filter(email__icontains=filters['email'])
        
        # Convert to DCI Person format
        persons = [
            PersonConverter.individual_to_dci_person(individual)
            for individual in queryset[:100]  # Limit to 100 results
        ]
        
    except ImportError:
        # Individual module not installed
        return Response(
            {
                'header': {
                    'status': 'error',
                    'message': 'Individual module not available'
                }
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except Exception as e:
        return Response(
            {
                'header': {
                    'status': 'error',
                    'message': str(e)
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Build response
    response_data = DCISearchResponseSerializer.create_response(
        request_data=request.data,
        persons=persons,
        transaction_id=transaction_id,
        reference_id=reference_id
    )

    return Response(response_data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['DCI Registry'],
    summary='Async Search for Person records',
    description='''
    Asynchronously search for Person records following the DCI standard.

    This endpoint returns an immediate 202 ACK response while queuing the search task.
    Once completed, it POSTs the search array callback back to standard sender_uri.
    ''',
    request=DCISearchRequestSerializer,
    responses={
        202: DCISearchResponseSerializer,
    }
)
@api_view(['POST'])
@permission_classes([DCIPersonPermissions])
def async_search(request):
    """
    DCI async search endpoint for Person records.
    POST /api/dci/reg/search
    """
    # Validate request
    serializer = DCISearchRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                'header': {
                    'status': 'error',
                    'message': 'Invalid request format'
                },
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
            
        # Queue background processing
        from ..tasks import BackgroundSearchTask
        task = BackgroundSearchTask(
            request_data=request.data,
            search_requests=search_requests
        )
        task.start()
        
    except Exception as e:
        return Response(
            {
                'header': {
                    'status': 'error',
                    'message': str(e)
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Return immediate ACK
    response_data = DCISearchResponseSerializer.create_ack_response(
        request_data=request.data,
        transaction_id=transaction_id
    )
    
    return Response(response_data, status=status.HTTP_202_ACCEPTED)