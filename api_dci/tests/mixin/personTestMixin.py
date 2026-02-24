"""
Person Test Mixin

Provides test data and utilities specific to DCI Person tests.
"""
from datetime import date


class PersonTestMixin:
    """
    Mixin for Person-related tests.
    Provides test data creation and verification methods.
    """

    # Test constants
    _TEST_FIRST_NAME = "John"
    _TEST_LAST_NAME = "Doe"
    _TEST_DOB = "1990-01-15"
    _TEST_GENDER = "Male"
    _TEST_PHONE = "+1234567890"
    _TEST_EMAIL = "john.doe@example.com"

    def create_test_dci_person(self, **kwargs):
        """
        Create a test DCI Person dict with default or custom values.

        Args:
            **kwargs: Override default values

        Returns:
            dict: DCI Person object
        """
        person = {
            "@type": "Person",
            "id": kwargs.get("id", "test:person:123"),
            "firstName": kwargs.get("firstName", self._TEST_FIRST_NAME),
            "lastName": kwargs.get("lastName", self._TEST_LAST_NAME),
            "dob": kwargs.get("dob", self._TEST_DOB),
            "gender": kwargs.get("gender", self._TEST_GENDER),
        }

        # Optional fields
        if "phone" in kwargs or hasattr(self, '_include_phone'):
            person["phone"] = kwargs.get("phone", self._TEST_PHONE)

        if "email" in kwargs or hasattr(self, '_include_email'):
            person["email"] = kwargs.get("email", self._TEST_EMAIL)

        return person

    def create_test_search_request(self, query_data=None, **kwargs):
        """
        Create a test DCI search request message.

        Args:
            query_data: Query person data (dict)
            **kwargs: Override default values

        Returns:
            dict: DCI search request
        """
        if query_data is None:
            query_data = {
                "firstName": self._TEST_FIRST_NAME,
                "lastName": self._TEST_LAST_NAME
            }

        return {
            "signature": kwargs.get("signature", {}),
            "header": {
                "version": kwargs.get("version", "1.0.0"),
                "message_id": kwargs.get("message_id", "test-msg-001"),
                "message_ts": kwargs.get("message_ts", "2024-02-21T10:00:00Z"),
                "action": kwargs.get("action", "search"),
                "sender_id": kwargs.get("sender_id", "test-sender"),
                "receiver_id": kwargs.get("receiver_id", "openimis"),
            },
            "message": {
                "transaction_id": kwargs.get("transaction_id", "test-txn-001"),
                "search_criteria": {
                    "reg_type": kwargs.get("reg_type", "person"),
                    "query_type": kwargs.get("query_type", "sync"),
                    "query": query_data
                }
            }
        }

    def verify_dci_person(self, person_data, expected_values=None):
        """
        Verify that person data has correct structure and values.

        Args:
            person_data: DCI Person dict to verify
            expected_values: Dict of expected values (optional)
        """
        # Verify required fields
        self.assertIn('@type', person_data)
        self.assertEqual(person_data['@type'], 'Person')
        self.assertIn('id', person_data)

        # Verify expected values if provided
        if expected_values:
            for key, expected_value in expected_values.items():
                if key in person_data:
                    self.assertEqual(person_data[key], expected_value,
                                   f"Mismatch in {key}: expected {expected_value}, got {person_data[key]}")
