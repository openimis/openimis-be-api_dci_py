"""
DCI API URL Configuration

Routes for DCI Registry Core API endpoints.
"""
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from .views import (
    sync_search, async_search, person_detail, DCILoginViewSet,
    subscribe, unsubscribe, notify, person_create, person_update
)

app_name = 'api_dci'

urlpatterns = [
    # Authentication endpoint
    path('login/', DCILoginViewSet.as_view({'post': 'create'}), name='login'),

    # DCI Registry Core API endpoints - Person operations
    path('registry/person', person_create, name='person-create'),
    path('registry/person/<str:person_id>', person_detail, name='person-detail'),
    path('registry/person/<str:person_id>/update', person_update, name='person-update'),
    path('registry/sync/search', sync_search, name='sync-search'),
    path('registry/async/search', async_search, name='async-search'),

    # DCI Registry Core API endpoints - Subscription operations
    path('registry/subscribe', subscribe, name='subscribe'),
    path('registry/unsubscribe', unsubscribe, name='unsubscribe'),
    path('registry/notify', notify, name='notify'),

    # OpenAPI documentation endpoints
    path('docs/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/swagger/', SpectacularSwaggerView.as_view(url_name='api_dci:schema'), name='swagger-ui'),
    path('docs/redoc/', SpectacularRedocView.as_view(url_name='api_dci:schema'), name='redoc'),
]