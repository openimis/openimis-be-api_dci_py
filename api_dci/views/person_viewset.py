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
    message = validated_data['message']
    transaction_id = message['transaction_id']

    # Detect format: FR (search_request array) or IBR (direct search_criteria)
    if 'search_request' in message:
        # FR format
        search_request_list = message['search_request']

        # Validate search_request is not empty
        if not search_request_list or len(search_request_list) == 0:
            return Response(
                {
                    'header': {
                        'status': 'error',
                        'message': 'search_request array cannot be empty'
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        search_request = search_request_list[0]
        search_criteria = search_request['search_criteria']
        format_type = 'fr'
    else:
        # IBR format
        search_criteria = message['search_criteria']
        format_type = 'ibr'

    query = search_criteria['query']
    query_type = search_criteria.get('query_type', 'sync')

    # Build query for Individual model
    try:
        from individual.models import Individual

        # Start with all valid individuals
        queryset = Individual.objects.filter(is_deleted=False)

        # Handle different query types
        if query_type == 'expression':
            # FR expression query - extract actual search fields
            # Expression format: {"type": "...", "value": {"expression": {...}}}
            if isinstance(query, dict) and 'value' in query:
                query_value = query.get('value', {})
                if 'expression' in query_value:
                    query = query_value['expression']

        # Apply search filters based on query content
        if isinstance(query, dict):
            # IBR simple format or extracted expression
            if 'firstName' in query:
                queryset = queryset.filter(first_name__icontains=query['firstName'])

            if 'lastName' in query:
                queryset = queryset.filter(last_name__icontains=query['lastName'])

            if 'dob' in query:
                queryset = queryset.filter(dob=query['dob'])

            if 'gender' in query:
                # Map DCI gender to OpenIMIS gender code
                gender_map = {
                    'Male': 'M',
                    'Female': 'F',
                    'Other': 'O'
                }
                gender_code = gender_map.get(query['gender'])
                if gender_code:
                    queryset = queryset.filter(gender__code=gender_code)

            if 'phone' in query:
                queryset = queryset.filter(phone__icontains=query['phone'])

            if 'email' in query:
                queryset = queryset.filter(email__icontains=query['email'])
        
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
        format_type=format_type
    )

    return Response(response_data, status=status.HTTP_200_OK)
