"""
Django app configuration for DCI API module.
"""
from django.apps import AppConfig

# Default registry type: "social" or "farmer"
# Can be overridden via MODULE_CONFIG in openimis.json or Django settings
DEFAULT_REGISTRY_TYPE = "farmer"


class ApiDciConfig(AppConfig):
    """
    Configuration class for the DCI API module.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_dci'
    verbose_name = 'DCI API'

    # Registry type: "social" (SRPerson) or "farmer" (FRPerson)
    registry_type = DEFAULT_REGISTRY_TYPE

    def ready(self):
        """
        Perform initialization when Django starts.
        """
        from django.conf import settings
        module_config = getattr(settings, 'API_DCI_CONFIG', {})
        ApiDciConfig.registry_type = module_config.get(
            'registry_type', DEFAULT_REGISTRY_TYPE
        )
