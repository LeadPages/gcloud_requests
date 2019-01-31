import json
import pytest

from httmock import HTTMock, urlmatch


@pytest.mark.parametrize("error_data,expected_tries", [
    ({"status": "SOME-UNHANDLED-STATUS"}, 1),
    ({"status": "RESOURCE_EXHAUSTED"}, 6),
    ({"status": "INTERNAL"}, 4),
    ({"status": "UNAVAILABLE"}, 6),
    ({"status": "DEADLINE_EXCEEDED"}, 6),
])
def test_pubsub_proxy_retries_retriable_json_errors(pubsub_proxy, error_data, expected_tries):
    # Given that I have a PubSub Proxy and a call database
    calls = []

    # And I've mocked the requests library to return errors on
    # requests to example.com
    @urlmatch(netloc=".*example.com")
    def request_handler(netloc, request):
        calls.append(1)
        return {
            "status_code": 500,
            "headers": {"content-type": "application/json"},
            "content": json.dumps({"error": error_data}),
        }

    with HTTMock(request_handler):
        # If I make a request
        pubsub_proxy.request("GET", "http://example.com")

        # I expect the endpoint to have been called some number of times
        assert sum(calls) == expected_tries
