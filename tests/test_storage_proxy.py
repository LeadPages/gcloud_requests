import json
import pytest

from httmock import HTTMock, urlmatch


@pytest.mark.parametrize("code,expected_tries", [
    (999, 1),
    (429, 11),
    (500, 6),
    (502, 6),
    (503, 6),
])
def test_storage_proxy_retries_retriable_json_errors(storage_proxy, code, expected_tries):
    # Given that I have a GCS Proxy and a call database
    calls = []

    # And I've mocked the requests library to return errors on
    # requests to example.com
    @urlmatch(netloc=".*example.com")
    def request_handler(netloc, request):
        calls.append(1)
        return {
            "status_code": 500,
            "headers": {"content-type": "application/json"},
            "content": json.dumps({"error": {"code": code}}),
        }

    with HTTMock(request_handler):
        # If I make a request
        response = storage_proxy.request("GET", "http://example.com")

        # I expect to get back a 500
        assert response.status_code == 500

        # I expect the endpoint to have been called some number of times
        assert sum(calls) == expected_tries


def test_storage_proxy_retries_on_502(storage_proxy):
    # Given that I have a GCS Proxy and a call database
    calls = []

    # And I've mocked the requests library to return 502s on requests
    # to example.com
    @urlmatch(netloc=".*example.com")
    def request_handler(netloc, request):
        calls.append(1)
        return {
            "status_code": 503,
            "headers": {"content-type": "text/html; charset=utf-8"},
            "content": "",
        }

    with HTTMock(request_handler):
        # If I make a request
        response = storage_proxy.request("GET", "http://example.com")

        # I expect to get back a 502
        assert response.status_code == 503

        # And the endpoint to have been called a total of 6 times
        assert sum(calls) == 6
