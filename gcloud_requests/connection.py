import logging
import gcloud.credentials

from .requests_connection import (
    BigQueryConnection,
    DatastoreConnection,
    DNSConnection,
    PubSubConnection,
    ResourceManagerConnection,
    StorageConnection
)

credentials = gcloud.credentials.get_credentials()

bigquery_connection = BigQueryConnection(credentials=credentials)
datastore_connection = DatastoreConnection(credentials=credentials)
dns_connection = DNSConnection(credentials=credentials)
pubsub_connection = PubSubConnection(credentials=credentials)
storage_connection = StorageConnection(credentials=credentials)

try:
    resource_manager_connection = ResourceManagerConnection(credentials=credentials)
except TypeError:
    logging.debug("Resource manager connection unavailable (cannot be used " \
                  "with service account credentials)")
