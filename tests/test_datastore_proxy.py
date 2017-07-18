import json
import pytest

from gcloud_requests.datastore import enter_transaction, exit_transaction
from google.rpc import code_pb2, status_pb2
from httmock import HTTMock, urlmatch


def make_status_code(code):
    status = status_pb2.Status()
    status.code = code
    return status.SerializeToString()


@pytest.mark.parametrize("error_data,expected_tries", [
    ({"status": "SOME-UNHANDLED-STATUS"}, 1),
    ({"status": "ABORTED"}, 6),
    ({"status": "INTERNAL"}, 2),
    ({"status": "UNKNOWN"}, 2),
    ({"status": "UNAVAILABLE"}, 6),
    ({"status": "DEADLINE_EXCEEDED"}, 6),
])
def test_datastore_proxy_retries_retriable_json_errors(datastore_proxy, error_data, expected_tries):
    # Given that I have a Datastore Proxy and a call database
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
        response, _ = datastore_proxy.request("http://example.com")

        # I expect the endpoint to have been called some number of times
        assert sum(calls) == expected_tries


@pytest.mark.parametrize("error_data,expected_tries", [
    (make_status_code(code_pb2.ABORTED), 6),
    (make_status_code(code_pb2.INTERNAL), 2),
    (make_status_code(code_pb2.UNKNOWN), 2),
    (make_status_code(code_pb2.UNAVAILABLE), 6),
    (make_status_code(code_pb2.DEADLINE_EXCEEDED), 6),
])
def test_datastore_proxy_retries_retriable_protobuf_errors(datastore_proxy, error_data, expected_tries):
    # Given that I have a Datastore Proxy and a call database
    calls = []

    # And I've mocked the requests library to return errors on
    # requests to example.com
    @urlmatch(netloc=".*example.com")
    def request_handler(netloc, request):
        calls.append(1)
        return {
            "status_code": 500,
            "headers": {"content-type": "application/x-protobuf"},
            "content": error_data,
        }

    with HTTMock(request_handler):
        # If I make a request
        response, _ = datastore_proxy.request("http://example.com")

        # I expect the endpoint to have been called some number of times
        assert sum(calls) == expected_tries


def test_datastore_proxy_does_not_retry_invalid_json(datastore_proxy):
    # Given that I have a Datastore Proxy and a call database
    calls = []

    # And I've mocked the requests library to return errors on
    # requests to example.com
    @urlmatch(netloc=".*example.com")
    def request_handler(netloc, request):
        calls.append(1)
        return {
            "status_code": 500,
            "headers": {"content-type": "application/json"},
            "content": {"foo": 42},
        }

    with HTTMock(request_handler):
        # If I make a request
        response, _ = datastore_proxy.request("http://example.com")

        # I expect the endpoint to have been called once
        assert sum(calls) == 1


def test_datastore_proxy_retries_on_502(datastore_proxy):
    # Given that I have a Datastore Proxy and a call database
    calls = []

    # And I've mocked the requests library to return 502s on requests
    # to example.com
    @urlmatch(netloc=".*example.com")
    def request_handler(netloc, request):
        calls.append(1)
        return {
            "status_code": 502,
            "headers": {"content-type": "text/html; charset=utf-8"},
        }

    with HTTMock(request_handler):
        # If I make a request
        response, _ = datastore_proxy.request("http://example.com")

        # I expect to get back a 502
        assert response.status == 502

        # And the endpoint to have been called a total of 6 times
        assert sum(calls) == 6


def test_datastore_proxy_does_not_retry_aborted_statuses_while_in_transaction(datastore_proxy):
    # Given that I have a Datastore Proxy and a call database
    calls = []

    # And I've mocked the requests library to return errors on
    # requests to example.com
    @urlmatch(netloc=".*example.com")
    def request_handler(netloc, request):
        calls.append(1)
        return {
            "status_code": 500,
            "headers": {"content-type": "application/json"},
            "content": json.dumps({"error": {"status": "ABORTED"}}),
        }

    with HTTMock(request_handler):
        # If I enter a transaction
        enter_transaction()

        try:
            # Then make a request
            response, _ = datastore_proxy.request("http://example.com")

            # I expect the endpoint to only get called once
            assert sum(calls) == 1
        finally:
            exit_transaction()
