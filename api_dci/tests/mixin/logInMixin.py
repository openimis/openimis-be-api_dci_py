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
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
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

        # Grant required DCI API permissions
        self._grant_dci_permissions(user)

        return user

    def _grant_dci_permissions(self, user):
        """
        Grant required permissions for DCI API testing.

        Args:
            user: User instance to grant permissions to
        """
        # Check if user is valid
        if not user or not hasattr(user, 'user_permissions'):
            return

        try:
            from django.contrib.auth.models import Permission
            from django.contrib.contenttypes.models import ContentType

            # Try to get Individual content type, fall back to a generic one
            content_type = None
            try:
                from individual.models import Individual
                content_type = ContentType.objects.get_for_model(Individual)
            except (ImportError, Exception):
                pass

            if content_type is None:
                # Use ContentType for the auth User model as a generic fallback
                from django.contrib.auth import get_user_model
                content_type = ContentType.objects.get_for_model(get_user_model())

            # Required permissions for DCI API
            permission_codenames = [
                'gql_query_individuals_perms',
                'gql_mutation_create_individuals_perms',
                'gql_mutation_update_individuals_perms',
                'gql_mutation_delete_individuals_perms',
            ]

            for codename in permission_codenames:
                # Try to get or create permission
                permission, _ = Permission.objects.get_or_create(
                    codename=codename,
                    defaults={
                        'name': f'Can {codename.replace("gql_", "").replace("_perms", "")}',
                        'content_type': content_type
                    }
                )

                # Check if user already has this permission
                if not user.user_permissions.filter(id=permission.id).exists():
                    user.user_permissions.add(permission)

            # Django caches permissions on the user object after the first has_perm call.
            # Clear the cache so newly added permissions take effect immediately.
            for cache_attr in ('_perm_cache', '_user_perm_cache', '_dci_perm_cache'):
                if hasattr(user, cache_attr):
                    delattr(user, cache_attr)

        except Exception:
            # If permission setup fails, silently skip
            # (Tests will fail with 403 if permissions are really needed)
            pass

    def login(self):
        """
        Perform login and set authentication token.

        Returns:
            bool: True if login successful
        """
        if not self.test_user:
            self.test_user = self.get_or_create_user_api()

        # Re-fetch the user from DB so Django loads a fresh permission set
        # (avoids stale permission cache from earlier has_perm calls)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            self.test_user = User.objects.get(pk=self.test_user.pk)
        except Exception:
            pass

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
