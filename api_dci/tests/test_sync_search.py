"""
Integration tests for DCI Person Sync Search API

Tests the DCI /registry/sync/search endpoint with full request/response cycle.
"""
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from api_dci.tests.mixin import DCIApiTestMixin, PersonTestMixin, LogInMixin


class SyncSearchAPITestCase(DCIApiTestMixin, PersonTestMixin, LogInMixin, APITestCase):
    """
    Test cases for Person DCI Sync Search API endpoint.
    Tests SPDCI FR v1.0.0 sync search functionality.
    """

    base_url = "/api/api_dci/registry/sync/search"

    def setUp(self):
        """Set up test data."""
        super().setUp()
        # Create test user and authenticate
        self.test_user = self.get_or_create_user_api()
        self.login()

        # Create test Individual records
        try:
            from individual.models import Individual
            from core.models import Gender

            # Get or create gender
            male_gender, _ = Gender.objects.get_or_create(code='M', defaults={'gender': 'Male'})
            female_gender, _ = Gender.objects.get_or_create(code='F', defaults={'gender': 'Female'})

            # Create test individuals
            self.individual1 = Individual.objects.create(
                first_name="John",
                last_name="Doe",
                dob="1990-01-15",
                gender=male_gender,
                phone="+1234567890",
                email="john.doe@example.com",
                user_created=self.test_user,
                user_updated=self.test_user
            )

            self.individual2 = Individual.objects.create(
                first_name="Jane",
                last_name="Smith",
                dob="1985-06-20",
                gender=female_gender,
                phone="+0987654321",
                email="jane.smith@example.com",
                user_created=self.test_user,
                user_updated=self.test_user
            )

            self.individual3 = Individual.objects.create(
                first_name="John",
                last_name="Smith",
                dob="1992-03-10",
                gender=male_gender,
                user_created=self.test_user,
                user_updated=self.test_user
            )

            self.has_individual_module = True
        except ImportError:
            self.has_individual_module = False
            self.skipTest("Individual module not available")

    def tearDown(self):
        """Clean up test data."""
        if self.has_individual_module:
            try:
                from individual.models import Individual
                Individual.objects.filter(
                    first_name__in=["John", "Jane"]
                ).delete()
            except:
                pass

    def test_sync_search_valid_request(self):
        """Test sync search with valid FR format request."""
        request_data = {
            "signature": "",
            "header": {
                "version": "1.0.0",
                "message_id": "test-msg-001",
                "message_ts": "2026-03-24T10:00:00Z",
                "action": "search",
                "sender_id": "test-sender",
                "receiver_id": "openimis"
            },
            "message": {
                "transaction_id": "txn-test-001",
                "search_request": [
                    {
                        "reference_id": "ref-001",
                        "timestamp": "2026-03-24T10:00:00Z",
                        "search_criteria": {
                            "query_type": "sync",
                            "query": {
                                "@type": "Person"
                            }
                        }
                    }
                ]
            }
        }

        response = self.client.post(
            self.base_url,
            data=request_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        # Verify response structure
        self.assertIn('header', response_data)
        self.assertIn('message', response_data)
        self.assertEqual(response_data['header']['status'], 'succ')
        self.assertEqual(response_data['header']['action'], 'on-search')

    def test_sync_search_by_first_name(self):
        """Test search by first name only."""
        request_data = {
            "signature": "",
            "header": {
                "version": "1.0.0",
                "message_id": "test-msg-002",
                "message_ts": "2026-03-24T10:00:00Z",
                "action": "search",
                "sender_id": "test-sender",
                "receiver_id": "openimis"
            },
            "message": {
                "transaction_id": "txn-test-002",
                "search_request": [
                    {
                        "reference_id": "ref-002",
                        "timestamp": "2026-03-24T10:00:00Z",
                        "search_criteria": {
                            "query_type": "sync",
                            "query": {
                                "@type": "Person",
                                "firstName": "John"
                            }
                        }
                    }
                ]
            }
        }

        response = self.client.post(
            self.base_url,
            data=request_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        # Should return 2 Johns (John Doe and John Smith)
        search_response = response_data['message']['search_response'][0]
        reg_records = search_response['data']['reg_records']
        self.assertGreaterEqual(len(reg_records), 2)

    def test_sync_search_invalid_format(self):
        """Test sync search with invalid request format."""
        invalid_request = {
            "header": {
                "version": "1.0.0"
                # Missing required fields
            }
        }

        response = self.client.post(
            self.base_url,
            data=invalid_request,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn('header', response_data)
        self.assertEqual(response_data['header']['status'], 'error')

    def test_sync_search_predicate_query(self):
        """Test SPDCI predicate query type."""
        request_data = {
            "signature": "",
            "header": {
                "version": "1.0.0",
                "message_id": "test-msg-predicate",
                "message_ts": "2026-03-24T10:00:00Z",
                "action": "search",
                "sender_id": "test-sender",
                "receiver_id": "openimis"
            },
            "message": {
                "transaction_id": "txn-predicate-001",
                "search_request": [
                    {
                        "reference_id": "ref-predicate",
                        "timestamp": "2026-03-24T10:00:00Z",
                        "search_criteria": {
                            "query_type": "predicate",
                            "query": [
                                {
                                    "seq_num": 1,
                                    "expression1": {
                                        "attribute_name": "firstName",
                                        "operator": "eq",
                                        "attribute_value": "Jane"
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }

        response = self.client.post(
            self.base_url,
            data=request_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        search_response = response_data['message']['search_response'][0]
        reg_records = search_response['data']['reg_records']

        # Should find Jane Smith
        self.assertGreaterEqual(len(reg_records), 1)
        self.assertTrue(any(r.get('name', {}).get('given_name') == 'Jane' for r in reg_records))

    def test_sync_search_no_results(self):
        """Test search when no matching records found."""
        request_data = {
            "signature": "",
            "header": {
                "version": "1.0.0",
                "message_id": "test-msg-no-results",
                "message_ts": "2026-03-24T10:00:00Z",
                "action": "search",
                "sender_id": "test-sender",
                "receiver_id": "openimis"
            },
            "message": {
                "transaction_id": "txn-no-results",
                "search_request": [
                    {
                        "reference_id": "ref-no-results",
                        "timestamp": "2026-03-24T10:00:00Z",
                        "search_criteria": {
                            "query_type": "sync",
                            "query": {
                                "@type": "Person",
                                "firstName": "NonExistentName12345"
                            }
                        }
                    }
                ]
            }
        }

        response = self.client.post(
            self.base_url,
            data=request_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data['header']['status'], 'succ')

        # Should return empty array
        search_response = response_data['message']['search_response'][0]
        reg_records = search_response['data']['reg_records']
        self.assertEqual(len(reg_records), 0)

    def test_sync_search_response_structure(self):
        """Test that response follows SPDCI FR format."""
        request_data = {
            "signature": "",
            "header": {
                "version": "1.0.0",
                "message_id": "test-structure",
                "message_ts": "2026-03-24T10:00:00Z",
                "action": "search",
                "sender_id": "test-sender",
                "receiver_id": "openimis"
            },
            "message": {
                "transaction_id": "txn-structure",
                "search_request": [
                    {
                        "reference_id": "ref-structure",
                        "timestamp": "2026-03-24T10:00:00Z",
                        "search_criteria": {
                            "query_type": "sync",
                            "query": {"@type": "Person"}
                        }
                    }
                ]
            }
        }

        response = self.client.post(
            self.base_url,
            data=request_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        # Verify FR response structure
        self.assertIn('signature', response_data)
        self.assertIn('header', response_data)
        self.assertIn('message', response_data)

        # Verify header fields
        header = response_data['header']
        self.assertIn('version', header)
        self.assertIn('message_id', header)
        self.assertIn('message_ts', header)
        self.assertIn('action', header)
        self.assertEqual(header['action'], 'on-search')
        self.assertIn('sender_id', header)
        self.assertIn('receiver_id', header)
        self.assertIn('status', header)
        self.assertEqual(header['status'], 'succ')

        # Verify message fields
        message = response_data['message']
        self.assertIn('transaction_id', message)
        self.assertIn('correlation_id', message)
        self.assertIn('search_response', message)

        # Verify search_response structure
        search_response = message['search_response'][0]
        self.assertIn('reference_id', search_response)
        self.assertIn('timestamp', search_response)
        self.assertIn('status', search_response)
        self.assertIn('data', search_response)

        # Verify data structure (FR format)
        data = search_response['data']
        self.assertIn('version', data)
        self.assertIn('reg_type', data)
        self.assertIn('reg_record_type', data)
        self.assertIn('reg_records', data)
        self.assertEqual(data['reg_type'], 'ns:org:RegistryType:FR')
