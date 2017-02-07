import requests
import time

from datetime import datetime
from gcloud.bigquery.connection import Connection as GCloudBigQueryConnection
from gcloud.datastore.connection import Connection as GCloudDatastoreConnection
from gcloud.dns.connection import Connection as GCloudDNSConnection
from gcloud.logging.connection import Connection as GCloudLoggingConnection
from gcloud.pubsub.connection import Connection as GCloudPubSubConnection
from gcloud.storage.connection import Connection as GCloudStorageConnection
from google.rpc import status_pb2
from requests.packages.urllib3.util.retry import Retry
from threading import local

from . import logger

_state = local()


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
    METHOD_WHITELIST = Retry.DEFAULT_METHOD_WHITELIST | frozenset(["POST"])

    def __new__(cls, credentials):
        # We want to both pass in the credentials to the instance and
        # at the same time decorate the resulting instance with those
        # credentials.
        if credentials.create_scoped_required():
            credentials = credentials.create_scoped(cls.SCOPE)
        instance = super(RequestsProxy, cls).__new__(cls)
        return credentials.authorize(instance)

    def __init__(self, credentials):
        # The connections property is required for the proxy to have
        # the correct shape.
        self.connections = {}
        self.credentials = credentials

    def _request(self, uri, method="GET", body=None, headers=None,
                 redirections=5, connection_type=None, retries=0):

        # NOTE: `retries` is the number of retries there have been so
        # far. It is passed in to/controlled by `_handle_response_error`.

        # Ensure we use one connection-pooling session per thread and
        # make use of requests' internal retry mechanism. It will
        # safely retry any requests that failed due to DNS lookup,
        # socket errors, etc.
        session = getattr(_state, "session", None)
        if session is None:
            retry_config = Retry(
                total=10,
                connect=10,
                read=5,
                method_whitelist=self.METHOD_WHITELIST
            )
            session = _state.session = requests.Session()
            adapter = _state.adapter = requests.adapters.HTTPAdapter(
                max_retries=retry_config
            )
            session.mount("http://", adapter)
            session.mount("https://", adapter)

        logger.debug("Using session={!r}, retries={!r}.".format(session, retries))
        response = session.request(
            method, uri, data=body, headers=headers,
            allow_redirects=redirections > 0,
            # NOTE: The connect timeout is set to 3.05 based on a
            # recommendation in requests' docs and the read timeout is
            # arbitrary.
            timeout=(3.05, 7)
        )
        if response.status_code >= 400:
            response = self._handle_response_error(
                response, retries,
                uri=uri, method=method,
                body=body, headers=headers,
                redirections=redirections,
                connection_type=connection_type
            )

        return ResponseProxy(response), response.content

    # NOTE: This instance method will get replaced with a decorated
    # version inside the connection object. The reason we keep both
    # around is so we can refer to the un-decorated version when
    # retrying requests.
    request = _request

    @property
    def _credentials_expire_in(self):
        """The number of seconds until the current set of credentials
        expire. 0 if the credentials have already expired.
        """
        if not self.credentials.token_expiry:
            return 0
        return max(0, (self.credentials.token_expiry - datetime.utcnow()).total_seconds())

    def _retry(self, retries, **kwargs):
        """This method inspects the oauth credentials to determine
        whether or not it is safe to retry a request without refreshing
        them. If it is not safe, this method will call the decorated
        request method, causing it to refresh its credentials and to
        make a valid request -- with the side effect of essentially
        restarting the current retry cycle.
        """
        expiration_window = self._credentials_expire_in
        logger.debug("Credentials will expire in %r...", expiration_window)

        if expiration_window < 15:
            logger.warning("Credentials expiration window is too small. Performing a hard retry...")
            return self.request(**kwargs)
        return self._request(retries=retries, **kwargs)

    def _handle_response_error(self, response, retries, **kwargs):
        """Provides a way for each connection wrapper to handle error
        responses.

        :param Response response:
          An instance of :class:`.requests.Response`.
        :param int retries:
          The number of times :meth:`.request` has been called so far.
        :param \**kwargs:
          The parameters with which :meth:`.request` was called. The
          `retries` parameter is excluded from `kwargs` intentionally.
        :returns:
          A :class:`.requests.Response`.
        """
        return response


class BigQueryRequestsProxy(RequestsProxy):
    SCOPE = GCloudBigQueryConnection.SCOPE


class DatastoreRequestsProxy(RequestsProxy):
    """A Datastore-specific RequestsProxy.

    This proxy handles retries according to [1].

    [1]: https://cloud.google.com/datastore/docs/concepts/errors.
    """

    SCOPE = GCloudDatastoreConnection.SCOPE

    # A mapping from numeric Google RPC error codes to known error
    # code strings.
    _PB_ERROR_CODES = {
        4: "DEADLINE_EXCEEDED",
        13: "INTERNAL",
        14: "UNAVAILABLE",
    }

    # A mapping from Datastore error states that can be retried to the
    # maximum number of times each one should be retried.
    _MAX_RETRIES = {
        "INTERNAL": 1,
        "UNAVAILABLE": 5,
        "DEADLINE_EXCEEDED": 5,
    }

    def _handle_response_error(self, response, retries, **kwargs):
        """Handles Datastore response errors according to their documentation.

        :param Response response:
          An instance of :class:`.requests.Response`.
        :param int retries:
          The number of times :meth:`.request` has been called so far.
        :param \**kwargs:
          The parameters with which :meth:`.request` was called. The
          `retries` parameter is excluded from `kwargs` intentionally.
        :returns:
          A :class:`.requests.Response`.

        .. [#] https://cloud.google.com/datastore/docs/concepts/errors
        """
        content_type = response.headers.get("content-type", "")
        if "application/x-protobuf" in content_type:
            logger.debug("Decoding protobuf response.")
            data = status_pb2.Status.FromString(response.content)
            status = self._PB_ERROR_CODES.get(data.code)
            error = {"status": status}

        elif "application/json" in content_type:
            logger.debug("Decoding json response.")
            data = response.json()
            error = data.get("error")
            if not error or not isinstance(error, dict):
                logger.warning("Unexpected error response from datastore: %r", data)
                return response

        else:
            logger.warning("Unexpected response from datastore: %r", response.text)
            return response

        status = error.get("status")
        max_retries = self._MAX_RETRIES.get(status)
        if max_retries is None or retries >= max_retries:
            return response

        backoff = min(0.0625 * 2 ** retries, 1.0)
        logger.debug("Sleeping for %r before retrying failed request...", backoff)
        time.sleep(backoff)

        logger.debug("Retrying failed request...")
        response_proxy, _ = self._retry(retries=retries + 1, **kwargs)
        return response_proxy.response


class DNSRequestsProxy(RequestsProxy):
    SCOPE = GCloudDNSConnection.SCOPE


class LoggingRequestsProxy(RequestsProxy):
    SCOPE = GCloudLoggingConnection.SCOPE


class PubSubRequestsProxy(RequestsProxy):
    SCOPE = GCloudPubSubConnection.SCOPE


class StorageRequestsProxy(RequestsProxy):
    SCOPE = GCloudStorageConnection.SCOPE
