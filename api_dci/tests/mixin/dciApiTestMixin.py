"""
DCI API Test Mixin

Provides common test utilities for DCI API endpoints.
"""
from rest_framework import status


class DCIApiTestMixin:
    """
    Mixin for DCI API tests.
    Provides common assertion methods and utilities.
    """

    def assertDCIResponseSuccess(self, response):
        """
        Assert that a DCI response is successful.

        Args:
            response: DRF Response object
        """
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertIn('header', response_data)
        self.assertEqual(response_data['header']['status'], 'success')

    def assertDCIResponseError(self, response, expected_status_code=None):
        """
        Assert that a DCI response contains an error.

        Args:
            response: DRF Response object
            expected_status_code: Expected HTTP status code (optional)
        """
        if expected_status_code:
            self.assertEqual(response.status_code, expected_status_code)

        response_data = response.json()
        self.assertIn('header', response_data)
        self.assertEqual(response_data['header']['status'], 'error')

    def assertDCIMessageStructure(self, response_data):
        """
        Assert that response has valid DCI message structure.

        Args:
            response_data: DCI message dict
        """
        # Check top-level structure
        self.assertIn('header', response_data)
        self.assertIn('message', response_data)

        # Check header fields
        header = response_data['header']
        self.assertIn('version', header)
        self.assertIn('message_id', header)
        self.assertIn('message_ts', header)
        self.assertIn('action', header)
        self.assertIn('sender_id', header)

    def assertPersonFields(self, person_data):
        """
        Assert that person data has required DCI Person fields.

        Args:
            person_data: DCI Person dict
        """
        self.assertIn('@type', person_data)
        self.assertEqual(person_data['@type'], 'Person')
        self.assertIn('id', person_data)

    def get_response_details(self, response_json):
        """
        Extract error/status details from DCI response.

        Args:
            response_json: Response JSON dict

        Returns:
            str: Error or status message
        """
        if 'header' in response_json and 'message' in response_json['header']:
            return response_json['header']['message']
        return None
