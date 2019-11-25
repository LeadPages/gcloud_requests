import json

import pytest
import requests

from httmock import HTTMock, urlmatch
from mock import Mock, patch


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

    # And I've mocked the requests library to return 503s on requests
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

        # I expect to get back a 503
        assert response.status_code == 503

        # And the endpoint to have been called a total of 6 times
        assert sum(calls) == 6


def test_storage_proxy_overrides_timeout_in_kwargs(storage_proxy):
    # Given a mocked requests session with a successful response
    with patch("gcloud_requests.proxy.RequestsProxy._get_session") as mock_get_session:
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.content = ""
        mock_session = Mock(spec=requests.Session)
        mock_session.request.return_value = mock_response
        mock_get_session.return_value = mock_session

        # If I make a request with a different timeout
        timeout = (123, 123)
        assert timeout != storage_proxy.TIMEOUT_CONFIG
        response = storage_proxy.request("GET", "http://example.com", timeout=timeout)

    # I expect a successful status code
    assert response.status_code == 200
    # And I expect the timeout to match the config instead of the provided kwarg
    assert mock_session.request.call_args.kwargs["timeout"] == storage_proxy.TIMEOUT_CONFIG
