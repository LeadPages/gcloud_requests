import gcloud.credentials

from .requests_connection import (
    BigQueryRequestsProxy,
    DatastoreRequestsProxy,
    DNSRequestsProxy,
    LoggingRequestsProxy,
    PubSubRequestsProxy,
    StorageRequestsProxy
)

credentials = gcloud.credentials.get_credentials()

bigquery_http = BigQueryRequestsProxy(credentials)
datastore_http = DatastoreRequestsProxy(credentials)
dns_http = DNSRequestsProxy(credentials)
logging_http = LoggingRequestsProxy(credentials)
pubsub_http = PubSubRequestsProxy(credentials)
storage_http = StorageRequestsProxy(credentials)
