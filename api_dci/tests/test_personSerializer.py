"""
Unit tests for Person Serializers

Tests the DCI Person serializers for validation and data transformation.
"""
from django.test import TestCase
from api_dci.serializers.person_serializer import (
    DCIPersonSerializer,
    DCISearchRequestSerializer,
    DCISearchResponseSerializer,
    DCIHeaderSerializer,
)


class DCIPersonSerializerTestCase(TestCase):
    """
    Test cases for DCIPersonSerializer.
    """

    def test_valid_person_serialization(self):
        """
        Test serialization of valid DCI Person data.
        """
        data = {
            "@type": "Person",
            "id": "test:person:123",
            "firstName": "John",
            "lastName": "Doe",
            "dob": "1990-01-15",
            "gender": "Male",
            "phone": "+1234567890",
            "email": "john.doe@example.com"
        }

        serializer = DCIPersonSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['firstName'], "John")
        self.assertEqual(serializer.validated_data['lastName'], "Doe")

    def test_minimal_person_serialization(self):
        """
        Test serialization with only required fields.
        """
        data = {
            "@type": "Person"
        }

        serializer = DCIPersonSerializer(data=data)
        # Should be valid as all fields are optional
        self.assertTrue(serializer.is_valid())

    def test_person_email_validation(self):
        """
        Test email field validation.
        """
        # Valid email
        data = {"email": "john@example.com"}
        serializer = DCIPersonSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # Invalid email
        data = {"email": "invalid-email"}
        serializer = DCIPersonSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)


class DCIHeaderSerializerTestCase(TestCase):
    """
    Test cases for DCIHeaderSerializer.
    """

    def test_valid_header_serialization(self):
        """
        Test serialization of valid DCI header.
        """
        data = {
            "version": "1.0.0",
            "message_id": "msg-001",
            "message_ts": "2024-02-21T10:00:00Z",
            "action": "search",
            "sender_id": "test-sender",
            "receiver_id": "openimis"
        }

        serializer = DCIHeaderSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['version'], "1.0.0")
        self.assertEqual(serializer.validated_data['action'], "search")

    def test_missing_required_header_fields(self):
        """
        Test validation with missing required fields.
        """
        data = {
            "version": "1.0.0"
            # Missing required fields
        }

        serializer = DCIHeaderSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('message_id', serializer.errors)
        self.assertIn('message_ts', serializer.errors)


class DCISearchRequestSerializerTestCase(TestCase):
    """
    Test cases for DCISearchRequestSerializer.
    """

    def test_valid_search_request(self):
        """
        Test serialization of valid search request.
        """
        data = {
            "signature": {},
            "header": {
                "version": "1.0.0",
                "message_id": "msg-001",
                "message_ts": "2024-02-21T10:00:00Z",
                "action": "search",
                "sender_id": "test-sender",
                "receiver_id": "openimis"
            },
            "message": {
                "transaction_id": "txn-001",
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

        serializer = DCISearchRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_search_request_missing_message(self):
        """
        Test validation with missing message section.
        """
        data = {
            "header": {
                "version": "1.0.0",
                "message_id": "msg-001",
                "message_ts": "2024-02-21T10:00:00Z",
                "action": "search",
                "sender_id": "test-sender"
            }
            # Missing message
        }

        serializer = DCISearchRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('message', serializer.errors)


class DCISearchResponseSerializerTestCase(TestCase):
    """
    Test cases for DCISearchResponseSerializer.
    """

    def test_create_response(self):
        """
        Test creating a DCI response from request and results.
        """
        request_data = {
            "signature": {},
            "header": {
                "version": "1.0.0",
                "message_id": "msg-001",
                "message_ts": "2024-02-21T10:00:00Z",
                "action": "search",
                "sender_id": "test-sender",
                "receiver_id": "openimis"
            }
        }

        persons = [
            {
                "@type": "Person",
                "id": "person:1",
                "firstName": "John",
                "lastName": "Doe"
            }
        ]

        response_data = DCISearchResponseSerializer.create_response(
            request_data=request_data,
            persons=persons,
            transaction_id="txn-001"
        )

        # Verify response structure
        self.assertIn('header', response_data)
        self.assertIn('message', response_data)

        # Verify header
        self.assertEqual(response_data['header']['action'], 'on-search')
        # SPDCI standard uses 'succ' not 'success'
        self.assertEqual(response_data['header']['status'], 'succ')
        self.assertEqual(response_data['header']['sender_id'], 'openimis')
        self.assertEqual(response_data['header']['receiver_id'], 'test-sender')

        # Verify message - SPDCI uses search_response array, not count
        self.assertEqual(response_data['message']['transaction_id'], 'txn-001')
        self.assertIn('search_response', response_data['message'])
        self.assertEqual(len(response_data['message']['search_response']), 1)

        # Verify total_count is in header (SPDCI standard)
        self.assertEqual(response_data['header']['total_count'], 1)
