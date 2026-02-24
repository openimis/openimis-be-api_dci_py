"""
DCI Login ViewSet

Provides JWT authentication endpoint for DCI API.
"""
from drf_spectacular.utils import extend_schema, inline_serializer
from graphql_jwt.utils import jwt_payload
from rest_framework import viewsets, serializers, exceptions
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.jwt import jwt_encode_user_key
from core.services import user_authentication


@extend_schema(
    tags=['Authentication'],
    request=inline_serializer(
        name='DCILoginRequest',
        fields={
            'username': serializers.CharField(help_text='Username'),
            'password': serializers.CharField(help_text='Password'),
        }
    ),
    responses={
        200: inline_serializer(
            name='DCILoginResponse',
            fields={
                'token': serializers.CharField(help_text='JWT access token'),
                'exp': serializers.IntegerField(help_text='Token expiration timestamp'),
            }
        ),
        400: inline_serializer(
            name='DCILoginError400',
            fields={
                'error': serializers.CharField(help_text='Error message'),
            }
        ),
        401: inline_serializer(
            name='DCILoginError401',
            fields={
                'error': serializers.CharField(help_text='Authentication failed'),
            }
        ),
    },
    description='Authenticate and obtain JWT token for DCI API access'
)
class DCILoginViewSet(viewsets.ViewSet):
    """
    ViewSet for DCI API authentication.

    This endpoint provides JWT token authentication for the DCI API.
    The token should be included in subsequent requests using the
    Authorization header: `Bearer <token>`
    """
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        """
        Authenticate user and return JWT token.

        Request body:
        {
            "username": "string",
            "password": "string"
        }

        Success response (200):
        {
            "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "exp": 1708778400
        }
        """
        data = request.data
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return Response(
                {"error": "Both username and password are required"},
                status=400
            )

        try:
            request.user = user_authentication(request, username, password)
        except exceptions.ParseError as e:
            return Response({"error": str(e)}, status=400)
        except exceptions.AuthenticationFailed as e:
            return Response({"error": str(e)}, status=401)

        if request.user:
            # Generate JWT payload
            payload = jwt_payload(user=request.user)
            # Encode token
            token = jwt_encode_user_key(payload=payload, context=request)

            if token:
                return Response(
                    data={
                        "token": token,
                        "exp": payload["exp"],
                    },
                    status=200
                )

            return Response(
                {"error": "Failed to generate token"},
                status=401
            )

        return Response(
            {"error": "Invalid credentials"},
            status=400
        )
