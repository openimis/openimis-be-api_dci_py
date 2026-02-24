"""
Django app configuration for DCI API module.
"""
from django.apps import AppConfig


class ApiDciConfig(AppConfig):
    """
    Configuration class for the DCI API module.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_dci'
    verbose_name = 'DCI API'

    def ready(self):
        """
        Perform initialization when Django starts.
        """
        pass
