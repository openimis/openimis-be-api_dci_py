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
    transaction_id = validated_data['message']['transaction_id']
    search_criteria = validated_data['message']['search_criteria']
    query = search_criteria['query']
    
    # Build query for Individual model
    try:
        from individual.models import Individual
        
        # Start with all valid individuals
        queryset = Individual.objects.filter(is_deleted=False)
        
        # Apply search filters
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
        transaction_id=transaction_id
    )
    
    return Response(response_data, status=status.HTTP_200_OK)