import logging
import requests

from gcloud.datastore.connection import Connection as GCloudDatastoreConnection
from gcloud.connection import Connection as GCloudConnection
from gcloud.storage.connection import Connection as GCloudStorageConnection

logger = logging.getLogger(__file__)


class ResponseProxy(object):
    def __init__(self, response):
        self.response = response

    def __getitem__(self, key):
        if key == "status":
            return str(self.status)

        return self.response.headers[key]

    @property
    def status(self):
        return self.response.status_code


class RequestsProxy(object):
    """Wraps a ``requests`` library :class:`.Session` instance and
    exposes a `request` method that is compatible with the
    ``httplib2`` `request` method.
    """

    def __init__(self):
        self.session = requests.Session()

    def request(self, uri, method="GET", body=None, headers=None,
                redirections=5, connection_type=None):
        response = self.session.request(
            method, uri, data=body, headers=headers,
            allow_redirects=redirections > 0,
        )
        return ResponseProxy(response), response.content


class RequestsConnectionMixin(GCloudConnection):
    """This mixin injects itself into the MRO of any subclass of
    :class:`.GCloudConnection` and overwrites the :meth:`.http` property
    so that a :class:`.RequestsProxy` is used instead of an ``httplib2``
    request object.
    """

    REQUESTS_PROXY_KEY = "__requests_proxy__"

    @property
    def http(self):
        if not hasattr(self, self.REQUESTS_PROXY_KEY):
            setattr(self, self.REQUESTS_PROXY_KEY, RequestsProxy())

            self._http = getattr(self, self.REQUESTS_PROXY_KEY)
            if self._credentials:
                self._http = self._credentials.authorize(self._http)

        return self._http


class DatastoreConnection(
        GCloudDatastoreConnection,
        RequestsConnectionMixin):
    "A datastore-compatible connection."


class StorageConnection(
        GCloudStorageConnection,
        RequestsConnectionMixin):
    "A Storage-compatible connection."
