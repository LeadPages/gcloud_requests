import atexit
import logging
import requests
import time

import google.auth

from functools import partial
from google.rpc import status_pb2
from google.auth.credentials import with_scopes_if_required
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request as AuthRequest
from requests.packages.urllib3.util.retry import Retry
from threading import local

from .credentials_watcher import CredentialsWatcher

_state = local()
_refresh_status_codes = (401,)
_max_refresh_attempts = 5
_credentials_watcher = CredentialsWatcher()
atexit.register(_credentials_watcher.stop)


class RequestsProxy(object):
    """Wraps a ``requests`` library :class:`.Session` instance and
    exposes a compatible `request` method.
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
    CONNECTION_POOL_SIZE = 32

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
            credentials = google.auth.default()[0]
            credentials = with_scopes_if_required(credentials, self.SCOPE)

        self.logger = logger or logging.getLogger(type(self).__name__)
        self.credentials = credentials
        _credentials_watcher.watch(credentials)

    def __del__(self):
        _credentials_watcher.unwatch(self.credentials)

    def request(self, method, url, data=None, headers=None, retries=0, refresh_attempts=0, **kwargs):
        session = self._get_session()
        headers = headers.copy() if headers is not None else {}
        auth_request = AuthRequest(session=session)
        retry_auth = partial(
            self.request,
            url=url, method=method,
            data=data, headers=headers,
            refresh_attempts=refresh_attempts + 1,
            retries=0,  # Retries intentionally get reset to 0.
            **kwargs
        )

        try:
            self.credentials.before_request(auth_request, method, url, headers)
        except RefreshError:
            if refresh_attempts < _max_refresh_attempts:
                return retry_auth()
            raise

        # Do not allow multiple timeout kwargs.
        kwargs["timeout"] = self.TIMEOUT_CONFIG

        response = session.request(method, url, data=data, headers=headers, **kwargs)
        if response.status_code in _refresh_status_codes and refresh_attempts < _max_refresh_attempts:
            self.logger.info(
                "Refreshing credentials due to a %s response. Attempt %s/%s.",
                response.status_code, refresh_attempts + 1, _max_refresh_attempts
            )

            try:
                self.credentials.refresh(auth_request)
            except RefreshError:
                pass

            return retry_auth()

        elif response.status_code >= 400:
            response = self._handle_response_error(
                response, retries,
                url=url, method=method,
                data=data, headers=headers,
                **kwargs
            )

        return response

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
                pool_connections=self.CONNECTION_POOL_SIZE,
                pool_maxsize=self.CONNECTION_POOL_SIZE,
            )
            session.mount("http://", adapter)
            session.mount("https://", adapter)
        return session

    def _handle_response_error(self, response, retries, **kwargs):
        r"""Provides a way for each connection wrapper to handle error
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
        error = self._convert_response_to_error(response)
        if error is None:
            return response

        max_retries = self._max_retries_for_error(error)
        if max_retries is None or retries >= max_retries:
            return response

        backoff = min(0.0625 * 2 ** retries, 1.0)
        self.logger.warning("Sleeping for %r before retrying failed request...", backoff)
        time.sleep(backoff)

        retries += 1
        self.logger.warning("Retrying failed request. Attempt %d/%d.", retries, max_retries)

        return self.request(retries=retries, **kwargs)

    def _convert_response_to_error(self, response):
        """Subclasses may override this method in order to influence
        how errors are parsed from the response.

        Parameters:
          response(Response): The response object.

        Returns:
          object or None: Any object for which a max retry count can
          be retrieved or None if the error cannot be handled.
        """
        content_type = response.headers.get("content-type", "")
        if "application/x-protobuf" in content_type:
            self.logger.debug("Decoding protobuf response.")
            data = status_pb2.Status.FromString(response.content)
            status = self._PB_ERROR_CODES.get(data.code)
            error = {"status": status}
            return error

        elif "application/json" in content_type:
            self.logger.debug("Decoding json response.")
            data = response.json()
            error = data.get("error")
            if not error or not isinstance(error, dict):
                self.logger.warning("Unexpected error response: %r", data)
                return None
            return error

        self.logger.warning("Unexpected response: %r", response.text)
        return None

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
