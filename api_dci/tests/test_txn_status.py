"""
Unit tests for DCI Transaction Status API

Tests the DCI /registry/txn/status endpoint.
"""
from rest_framework.test import APITestCase
from rest_framework import status
from api_dci.tests.mixin import DCIApiTestMixin, LogInMixin


class TxnStatusAPITestCase(DCIApiTestMixin, LogInMixin, APITestCase):
    """
    Test cases for DCI txn status endpoint.
    Tests SPDCI FR v1.0.0 transaction status functionality.
    """

    url = "/api/api_dci/registry/txn/status"

    def setUp(self):
        super().setUp()
        self.test_user = self.get_or_create_user_api()
        self.login()

    def _valid_payload(self, txn_id="txn-001", ref_id="ref-001"):
        return {
            "signature": "",
            "header": {
                "version": "1.0.0",
                "message_id": "msg-txn-001",
                "message_ts": "2026-01-01T00:00:00Z",
                "action": "txn-status",
                "sender_id": "test-sender",
                "receiver_id": "openimis",
                "is_msg_encrypted": False,
            },
            "message": {
                "transaction_id": txn_id,
                "txnstatus_request": {
                    "reference_id": ref_id,
                    "txn_type": "search",
                    "attribute_type": "transaction_id",
                    "attribute_value": txn_id,
                },
            },
        }

    def test_valid_request_returns_200(self):
        """Valid txn status request returns 200 with ACK."""
        response = self.client.post(self.url, data=self._valid_payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_has_ack_status(self):
        """Response message contains ACK status."""
        response = self.client.post(self.url, data=self._valid_payload(), format='json')
        self.assertEqual(response.data['message']['ack_status'], 'ACK')

    def test_response_header_action_is_on_txn_status(self):
        """Response header action is on-txn-status."""
        response = self.client.post(self.url, data=self._valid_payload(), format='json')
        self.assertEqual(response.data['header']['action'], 'on-txn-status')

    def test_response_correlation_id_matches_transaction_id(self):
        """Response correlation_id echoes the request transaction_id."""
        txn_id = "txn-test-abc-123"
        response = self.client.post(self.url, data=self._valid_payload(txn_id=txn_id), format='json')
        self.assertEqual(response.data['message']['correlation_id'], txn_id)

    def test_response_sender_receiver_swapped(self):
        """Response sender/receiver are swapped from the request."""
        response = self.client.post(self.url, data=self._valid_payload(), format='json')
        self.assertEqual(response.data['header']['receiver_id'], 'test-sender')
        self.assertEqual(response.data['header']['sender_id'], 'openimis')

    def test_unauthenticated_request_rejected(self):
        """Unauthenticated request returns 401 or 403."""
        self.client.logout()
        response = self.client.post(self.url, data=self._valid_payload(), format='json')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_missing_transaction_id_returns_400(self):
        """Request missing transaction_id returns 400."""
        payload = self._valid_payload()
        del payload['message']['transaction_id']
        response = self.client.post(self.url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_txnstatus_request_returns_400(self):
        """Request missing txnstatus_request returns 400."""
        payload = self._valid_payload()
        del payload['message']['txnstatus_request']
        response = self.client.post(self.url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_header_returns_400(self):
        """Request missing header returns 400."""
        payload = self._valid_payload()
        del payload['header']
        response = self.client.post(self.url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_content_type_is_json(self):
        """Response Content-Type is application/json."""
        response = self.client.post(self.url, data=self._valid_payload(), format='json')
        self.assertIn('application/json', response.headers.get('Content-Type', ''))
