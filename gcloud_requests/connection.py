import gcloud.credentials

from .requests_connection import (
    RequestsProxy,
    DatastoreRequestsProxy
)

credentials = gcloud.credentials.get_credentials()
requests_http = RequestsProxy(credentials)
datastore_http = DatastoreRequestsProxy(credentials)
