import threading
import requests
import logging

logger = logging.getLogger(__name__)

class BackgroundSearchTask(threading.Thread):
    """
    Background thread to process DCI async search requests.
    Once completed, sends a POST request with the results to the sender_uri callback.
    """
    
    def __init__(self, request_data, search_requests, results_store=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.daemon = True
        self.request_data = request_data
        self.search_requests = search_requests
        self.results_store = results_store
        
    def run(self):
        transaction_id = self.request_data.get('message', {}).get('transaction_id')
        try:
            from .views.person_viewset import _build_queryset_from_search, _convert_to_persons
            from .serializers.person_serializer import DCISearchResponseSerializer

            sender_uri = self.request_data.get('header', {}).get('sender_uri')

            search_request = self.search_requests[0]
            reference_id = search_request.get('reference_id', '')

            queryset, offset, page_size = _build_queryset_from_search(search_request)
            persons = _convert_to_persons(queryset, offset, page_size)

            response_data = DCISearchResponseSerializer.create_response(
                request_data=self.request_data,
                persons=persons,
                transaction_id=transaction_id,
                reference_id=reference_id
            )

            # Store results for txn/status polling
            if self.results_store is not None and transaction_id:
                self.results_store[transaction_id] = {
                    'status': 'succ',
                    'result': response_data,
                }

            # POST callback to sender_uri if provided
            if sender_uri:
                requests.post(
                    sender_uri,
                    json=response_data,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )

        except Exception as e:
            logger.error(f"DCI Async Search background task failed: {str(e)}")
            if self.results_store is not None and transaction_id:
                self.results_store[transaction_id] = {
                    'status': 'rjct',
                    'error': str(e),
                }
