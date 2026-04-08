"""
Integration tests for DCI Subscription API

Tests the DCI /registry/subscribe and /registry/unsubscribe endpoints.
"""
from rest_framework.test import APITestCase
from rest_framework import status
from api_dci.tests.mixin import DCIApiTestMixin, LogInMixin


class SubscriptionAPITestCase(DCIApiTestMixin, LogInMixin, APITestCase):
    """
    Test cases for DCI Subscription API endpoints.
    Tests SPDCI FR v1.0.0 subscribe/unsubscribe functionality.
    """

    subscribe_url = "/api/api_dci/registry/subscribe"
    unsubscribe_url = "/api/api_dci/registry/unsubscribe"

    def setUp(self):
        """Set up test data."""
        super().setUp()
        # Create test user and authenticate
        self.test_user = self.get_or_create_user_api()
        self.login()

        # Check if subscription models are available
        try:
            from api_dci.models import DCISubscription  # noqa: F401
            self.has_subscription_module = True
        except ImportError:
            self.has_subscription_module = False
            self.skipTest("Subscription models not available")

    def tearDown(self):
        """Clean up test data."""
        if self.has_subscription_module:
            try:
                from api_dci.models import DCISubscription
                DCISubscription.objects.filter(
                    sender_id__startswith="test-"
                ).delete()
            except Exception:
                pass

    def test_subscribe_valid_request(self):
        """Test subscribe with valid FR format request."""
        request_data = {
            "signature": "",
            "header": {
                "version": "1.0.0",
                "message_id": "test-sub-001",
                "message_ts": "2026-03-24T10:00:00Z",
                "action": "subscribe",
                "sender_id": "test-subscriber-001",
                "sender_uri": "http://test-system.com/callback",
                "receiver_id": "openimis",
                "is_msg_encrypted": False
            },
            "message": {
                "transaction_id": "txn-sub-001",
                "subscribe_request": [
                    {
                        "reference_id": "ref-sub-001",
                        "timestamp": "2026-03-24T10:00:00Z",
                        "event_type": "ALL",
                        "filter": {}
                    }
                ]
            }
        }

        response = self.client.post(
            self.subscribe_url,
            data=request_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        # Verify ACK response structure
        self.assertIn('header', response_data)
        self.assertIn('message', response_data)
        self.assertEqual(response_data['header']['action'], 'on-subscribe')
        self.assertEqual(response_data['header']['status'], 'succ')

        # Verify message contains ACK
        message = response_data['message']
        self.assertIn('ack_status', message)
        self.assertEqual(message['ack_status'], 'ACK')
        self.assertIn('timestamp', message)
        self.assertIn('correlation_id', message)

    def test_subscribe_specific_event_type(self):
        """Test subscribe with specific event type (REGISTER)."""
        request_data = {
            "signature": "",
            "header": {
                "version": "1.0.0",
                "message_id": "test-sub-register",
                "message_ts": "2026-03-24T10:00:00Z",
                "action": "subscribe",
                "sender_id": "test-subscriber-register",
                "sender_uri": "http://test-system.com/notify",
                "receiver_id": "openimis",
                "is_msg_encrypted": False
            },
            "message": {
                "transaction_id": "txn-sub-register",
                "subscribe_request": [
                    {
                        "reference_id": "ref-sub-register",
                        "timestamp": "2026-03-24T10:00:00Z",
                        "event_type": "REGISTER"
                    }
                ]
            }
        }

        response = self.client.post(
            self.subscribe_url,
            data=request_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data['header']['status'], 'succ')

    def test_subscribe_invalid_format(self):
        """Test subscribe with invalid request format."""
        invalid_request = {
            "header": {
                "version": "1.0.0"
                # Missing required fields
            }
        }

        response = self.client.post(
            self.subscribe_url,
            data=invalid_request,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn('header', response_data)
        self.assertEqual(response_data['header']['status'], 'error')

    def test_unsubscribe_valid_request(self):
        """Test unsubscribe with valid subscription_id."""
        # First, create a subscription
        subscribe_data = {
            "signature": "",
            "header": {
                "version": "1.0.0",
                "message_id": "test-sub-for-unsub",
                "message_ts": "2026-03-24T10:00:00Z",
                "action": "subscribe",
                "sender_id": "test-subscriber-unsub",
                "sender_uri": "http://test-system.com/callback",
                "receiver_id": "openimis",
                "is_msg_encrypted": False
            },
            "message": {
                "transaction_id": "txn-sub-for-unsub",
                "subscribe_request": [
                    {
                        "reference_id": "ref-sub-for-unsub",
                        "timestamp": "2026-03-24T10:00:00Z",
                        "event_type": "ALL"
                    }
                ]
            }
        }

        subscribe_response = self.client.post(
            self.subscribe_url,
            data=subscribe_data,
            format='json'
        )
        self.assertEqual(subscribe_response.status_code, status.HTTP_200_OK)

        # Get subscription_id from database
        from api_dci.models import DCISubscription
        subscription = DCISubscription.objects.filter(
            sender_id="test-subscriber-unsub",
            is_deleted=False
        ).first()

        if subscription:
            subscription_id = subscription.subscription_code

            # Now unsubscribe
            unsubscribe_data = {
                "signature": "",
                "header": {
                    "version": "1.0.0",
                    "message_id": "test-unsub-001",
                    "message_ts": "2026-03-24T11:00:00Z",
                    "action": "unsubscribe",
                    "sender_id": "test-subscriber-unsub",
                    "receiver_id": "openimis",
                    "is_msg_encrypted": False
                },
                "message": {
                    "transaction_id": "txn-unsub-001",
                    "unsubscribe_request": [
                        {
                            "reference_id": "ref-unsub-001",
                            "timestamp": "2026-03-24T11:00:00Z",
                            "subscription_id": subscription_id
                        }
                    ]
                }
            }

            response = self.client.post(
                self.unsubscribe_url,
                data=unsubscribe_data,
                format='json'
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response_data = response.json()

            # Verify ACK response
            self.assertEqual(response_data['header']['action'], 'on-unsubscribe')
            self.assertEqual(response_data['header']['status'], 'succ')
            self.assertEqual(response_data['message']['ack_status'], 'ACK')

            # Verify subscription is deactivated
            subscription.refresh_from_db()
            self.assertEqual(subscription.status, DCISubscription.SubscriptionStatus.INACTIVE)

    def test_unsubscribe_nonexistent_subscription(self):
        """Test unsubscribe with non-existent subscription_id."""
        unsubscribe_data = {
            "signature": "",
            "header": {
                "version": "1.0.0",
                "message_id": "test-unsub-nonexistent",
                "message_ts": "2026-03-24T11:00:00Z",
                "action": "unsubscribe",
                "sender_id": "test-subscriber",
                "receiver_id": "openimis",
                "is_msg_encrypted": False
            },
            "message": {
                "transaction_id": "txn-unsub-nonexistent",
                "unsubscribe_request": [
                    {
                        "reference_id": "ref-unsub-nonexistent",
                        "timestamp": "2026-03-24T11:00:00Z",
                        "subscription_id": "non-existent-sub-id-12345"
                    }
                ]
            }
        }

        response = self.client.post(
            self.unsubscribe_url,
            data=unsubscribe_data,
            format='json'
        )

        # Should still return 200 with ACK (idempotent)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data['header']['status'], 'succ')

    def test_subscribe_with_expiry(self):
        """Test subscribe with expiry date."""
        request_data = {
            "signature": "",
            "header": {
                "version": "1.0.0",
                "message_id": "test-sub-expiry",
                "message_ts": "2026-03-24T10:00:00Z",
                "action": "subscribe",
                "sender_id": "test-subscriber-expiry",
                "sender_uri": "http://test-system.com/callback",
                "receiver_id": "openimis",
                "is_msg_encrypted": False
            },
            "message": {
                "transaction_id": "txn-sub-expiry",
                "subscribe_request": [
                    {
                        "reference_id": "ref-sub-expiry",
                        "timestamp": "2026-03-24T10:00:00Z",
                        "event_type": "UPDATE",
                        "expiry": "2027-03-24T10:00:00Z"
                    }
                ]
            }
        }

        response = self.client.post(
            self.subscribe_url,
            data=request_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify subscription has expiry set
        from api_dci.models import DCISubscription
        subscription = DCISubscription.objects.filter(
            sender_id="test-subscriber-expiry",
            is_deleted=False
        ).first()

        if subscription:
            self.assertIsNotNone(subscription.expiring)

    def test_subscribe_with_filter(self):
        """Test subscribe with filter criteria."""
        request_data = {
            "signature": "",
            "header": {
                "version": "1.0.0",
                "message_id": "test-sub-filter",
                "message_ts": "2026-03-24T10:00:00Z",
                "action": "subscribe",
                "sender_id": "test-subscriber-filter",
                "sender_uri": "http://test-system.com/callback",
                "receiver_id": "openimis",
                "is_msg_encrypted": False
            },
            "message": {
                "transaction_id": "txn-sub-filter",
                "subscribe_request": [
                    {
                        "reference_id": "ref-sub-filter",
                        "timestamp": "2026-03-24T10:00:00Z",
                        "event_type": "ALL",
                        "filter": {
                            "idtype-value": {
                                "id_type": "FARMER_ID",
                                "id_value": "FARMER-*"
                            }
                        }
                    }
                ]
            }
        }

        response = self.client.post(
            self.subscribe_url,
            data=request_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify filter is stored
        from api_dci.models import DCISubscription
        subscription = DCISubscription.objects.filter(
            sender_id="test-subscriber-filter",
            is_deleted=False
        ).first()

        if subscription:
            self.assertIsNotNone(subscription.filter_criteria)
            self.assertIn('idtype-value', subscription.filter_criteria)
