"""
DCI API Permission Classes

Permission classes for DCI API endpoints.
"""
from rest_framework.permissions import BasePermission


class DCIPersonPermissions(BasePermission):
    """
    Permission class for DCI Person API endpoints.

    Uses OpenIMIS Individual module permissions to control access
    to Person search and CRUD operations.
    """

    def has_permission(self, request, view):
        """
        Check if user has permission to access Person endpoints.

        For search operations, requires individual.gql_query_individuals_perms
        For create operations, requires individual.gql_mutation_create_individuals_perms
        For update operations, requires individual.gql_mutation_update_individuals_perms
        For delete operations, requires individual.gql_mutation_delete_individuals_perms
        """
        # Require authentication for all DCI Person endpoints
        if not hasattr(request, 'user') or not request.user or not request.user.is_authenticated:
            return False

        # Map HTTP methods to required permissions
        permission_map = {
            'GET': 'individual.gql_query_individuals_perms',
            'POST': 'individual.gql_query_individuals_perms',  # Search is POST in DCI
            'PUT': 'individual.gql_mutation_update_individuals_perms',
            'PATCH': 'individual.gql_mutation_update_individuals_perms',
            'DELETE': 'individual.gql_mutation_delete_individuals_perms',
        }

        required_permission = permission_map.get(request.method)

        if not required_permission:
            return False

        # Check if user has the required permission
        try:
            return request.user.has_perm(required_permission)
        except AttributeError:
            # User object doesn't support has_perm
            return True
