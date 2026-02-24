"""
LogIn Mixin for DCI tests

Provides authentication utilities for API tests.
"""
from rest_framework.test import APIClient


class LogInMixin:
    """
    Mixin for handling authentication in tests.
    """

    test_user = None
    _test_username = "test_dci_user"
    _test_password = "test_password_123"
    _auth_token = None

    def setUp(self):
        """
        Set up authentication for tests.
        """
        super().setUp()
        self.client = APIClient()

    def get_or_create_user_api(self):
        """
        Get or create a test user for API authentication.

        Returns:
            User: Test user instance
        """
        from django.contrib.auth import get_user_model
        from core.models import InteractiveUser

        User = get_user_model()

        try:
            user = User.objects.get(username=self._test_username)
        except User.DoesNotExist:
            # Create user
            user = User.objects.create_user(
                username=self._test_username,
                password=self._test_password
            )

            # Create associated InteractiveUser if needed
            try:
                InteractiveUser.objects.create(
                    login_name=self._test_username,
                    user=user
                )
            except Exception:
                pass  # InteractiveUser might not be required

        return user

    def login(self):
        """
        Perform login and set authentication token.

        Returns:
            bool: True if login successful
        """
        if not self.test_user:
            self.test_user = self.get_or_create_user_api()

        # Force authentication for the test client
        self.client.force_authenticate(user=self.test_user)
        return True

    def logout(self):
        """
        Logout and clear authentication.
        """
        self.client.force_authenticate(user=None)
        self._auth_token = None

    def load_user_data_from_json(self, json_path):
        """
        Load user credentials from JSON file.

        Args:
            json_path: Path to JSON file with credentials
        """
        # To be implemented if needed for loading test credentials
        # from JSON files like in FHIR R4 tests
        pass
