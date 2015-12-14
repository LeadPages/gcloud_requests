import logging
import requests
import time

from gcloud.datastore.connection import Connection as GCloudDatastoreConnection
from gcloud.connection import Connection as GCloudConnection
from gcloud.storage.connection import Connection as GCloudStorageConnection
from threading import local

logger = logging.getLogger(__file__)
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

    def __init__(self):
        # XXX: This is required for the proxy to have the correct shape.
        self.connections = {}

    def request(self, uri, method="GET", body=None, headers=None,
                redirections=5, connection_type=None, retries=0):

        # NOTE: `retries` is the number of retries there have been so
        # far. It is passed in to/controlled by `_handle_response_error`.

        # XXX: Ensure we use one connection-pooling session per thread.
        session = getattr(_state, "session", None)
        if session is None:
            session = _state.session = requests.Session()

        logger.debug("Using session {!r}.".format(session))
        response = session.request(
            method, uri, data=body, headers=headers,
            allow_redirects=redirections > 0,
            # XXX: The connect timeout is set to 3.05 based on a
            # recommendation in requests' docs and the read timeout is
            # arbitrary.
            timeout=(3.05, 15)
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


class DatastoreRequestsProxy(RequestsProxy):
    """A Datastore-specific RequestsProxy that handles retries according
    to https://cloud.google.com/datastore/docs/concepts/errors.
    """

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
        if response.status_code == 500 and retries < 1 or \
           response.status_code == 503 and retries < 4 or \
           response.status_code == 403 and retries < 2 or \
           response.status_code == 409 and retries < 1:
            backoff = 2 ** retries
            logger.debug("Sleeping for %r before retrying failed request...", backoff)
            time.sleep(backoff)
            logger.debug("Retrying failed request...")
            # XXX: We need to make sure we unwrap the response before we
            # return back to the `request` method.
            response_proxy, _ = self.request(retries=retries + 1, **kwargs)
            return response_proxy.response

        return response


class RequestsConnectionMixin(GCloudConnection):
    """This mixin injects itself into the MRO of any subclass of
    :class:`.GCloudConnection` and overwrites the :meth:`.http` property
    so that a :class:`.RequestsProxy` is used instead of an ``httplib2``
    request object.
    """

    REQUESTS_PROXY_CLASS = RequestsProxy
    REQUESTS_PROXY_KEY = "__requests_proxy__"

    @property
    def http(self):
        if not hasattr(self, self.REQUESTS_PROXY_KEY):
            setattr(self, self.REQUESTS_PROXY_KEY, self.REQUESTS_PROXY_CLASS())

            self._http = getattr(self, self.REQUESTS_PROXY_KEY)
            if self._credentials:
                self._http = self._credentials.authorize(self._http)

        return self._http


class DatastoreConnection(
        GCloudDatastoreConnection,
        RequestsConnectionMixin):
    "A datastore-compatible connection."

    REQUESTS_PROXY_CLASS = DatastoreRequestsProxy


class StorageConnection(
        GCloudStorageConnection,
        RequestsConnectionMixin):
    "A Storage-compatible connection."
