import logging
import requests
import time

from google.rpc import status_pb2
from google.auth.credentials import with_scopes_if_required
from google.auth.transport.requests import Request as AuthRequest
from google.cloud.credentials import get_credentials
from requests.packages.urllib3.util.retry import Retry
from threading import local

_state = local()
_refresh_status_codes = (401,)
_max_refresh_attempts = 2


class ResponseProxy(requests.structures.CaseInsensitiveDict):
    def __init__(self, response):
        super(ResponseProxy, self).__init__()
        self.response = response
        self.update(response.headers)
        self.update(status=str(self.status))

    @property
    def status(self):
        return self.response.status_code


class RequestsProxy(object):
    """Wraps a ``requests`` library :class:`.Session` instance and
    exposes a `request` method that is compatible with the
    ``httplib2`` `request` method.
    """

    SCOPE = None

    #: Determines how connection and read timeouts should be handled
    #: by this proxy.
    TIMEOUT_CONFIG = (3.05, 30)

    #: Determines how retries should be handled by this proxy.
    RETRY_CONFIG = Retry(
        total=10, connect=10, read=5,
        method_whitelist=Retry.DEFAULT_METHOD_WHITELIST | frozenset(["POST"])
    )

    #: The number of connections to pool per Session.
    CONNETION_POOL_SIZE = 32

    # A mapping from numeric Google RPC error codes to known error
    # code strings.
    _PB_ERROR_CODES = {
        2: "UNKNOWN",
        4: "DEADLINE_EXCEEDED",
        10: "ABORTED",
        13: "INTERNAL",
        14: "UNAVAILABLE",
    }

    def __init__(self, credentials=None, logger=None):
        if credentials is None:
            credentials = get_credentials()
            credentials = with_scopes_if_required(credentials, self.SCOPE)

        self.logger = logger or logging.getLogger(type(self).__name__)
        self.credentials = credentials
        self.auth_request = AuthRequest(session=self._get_session())

    def request(self, uri, method="GET", body=None, headers=None, redirections=5, connection_type=None, retries=0, refresh_attempts=0):   # noqa
        session = self._get_session()
        headers = headers.copy() if headers is not None else {}
        self.credentials.before_request(self.auth_request, method, uri, headers)

        response = session.request(
            method, uri, data=body, headers=headers,
            allow_redirects=redirections > 0,
            timeout=self.TIMEOUT_CONFIG,
        )
        if response.status_code in _refresh_status_codes and refresh_attempts < _max_refresh_attempts:
            self.logger.info(
                "Refreshing credentials due to a %s response. Attempt %s/%s.",
                response.status_code, refresh_attempts + 1, _max_refresh_attempts
            )
            self.credentials.refresh(self.auth_request)
            return self.request(
                uri=uri, method=method,
                body=body, headers=headers,
                redirections=redirections,
                connection_type=connection_type,
                refresh_attempts=refresh_attempts + 1,
                retries=0,  # Retries intentionally get reset to 0.
            )

        elif response.status_code >= 400:
            response = self._handle_response_error(
                response, retries,
                uri=uri, method=method,
                body=body, headers=headers,
                redirections=redirections,
                connection_type=connection_type
            )

        return ResponseProxy(response), response.content

    def _get_session(self):
        # Ensure we use one connection-pooling session per thread and
        # make use of requests' internal retry mechanism. It will
        # safely retry any requests that failed due to DNS lookup,
        # socket errors, etc.
        session = getattr(_state, "session", None)
        if session is None:
            session = _state.session = requests.Session()
            adapter = _state.adapter = requests.adapters.HTTPAdapter(
                max_retries=self.RETRY_CONFIG,
                pool_connections=self.CONNETION_POOL_SIZE,
                pool_maxsize=self.CONNETION_POOL_SIZE,
            )
            session.mount("http://", adapter)
            session.mount("https://", adapter)
        return session

    def _handle_response_error(self, response, retries, **kwargs):
        """Provides a way for each connection wrapper to handle error
        responses.

        Parameters:
          response(Response): An instance of :class:`.requests.Response`.
          retries(int): The number of times :meth:`.request` has been
            called so far.
          \**kwargs: The parameters with which :meth:`.request` was
            called.  The `retries` parameter is excluded from `kwargs`
            intentionally.

        Returns:
          requests.Response
        """
        content_type = response.headers.get("content-type", "")
        if "application/x-protobuf" in content_type:
            self.logger.debug("Decoding protobuf response.")
            data = status_pb2.Status.FromString(response.content)
            status = self._PB_ERROR_CODES.get(data.code)
            error = {"status": status}

        elif "application/json" in content_type:
            self.logger.debug("Decoding json response.")
            data = response.json()
            error = data.get("error")
            if not error or not isinstance(error, dict):
                self.logger.warning("Unexpected error response: %r", data)
                return response

        else:
            self.logger.warning("Unexpected response: %r", response.text)
            return response

        max_retries = self._max_retries_for_error(error)
        if max_retries is None or retries >= max_retries:
            return response

        backoff = min(0.0625 * 2 ** retries, 1.0)
        self.logger.warning("Sleeping for %r before retrying failed request...", backoff)
        time.sleep(backoff)

        retries += 1
        self.logger.warning("Retrying failed request. Attempt %d/%d.", retries, max_retries)
        response_proxy, _ = self.request(retries=retries, **kwargs)
        return response_proxy.response

    def _max_retries_for_error(self, error):
        """Subclasses may implement this method in order to influence
        how many times various error types should be retried.

        Parameters:
          error(dict): A dictionary containing a `status

        Returns:
          int or None: The max number of times this error should be
          retried or None if it shouldn't.
        """
        return None
