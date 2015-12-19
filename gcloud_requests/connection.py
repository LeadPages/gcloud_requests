import gcloud.credentials

from .requests_connection import (
    BigQueryConnection,
    DatastoreConnection,
    DNSConnection,
    PubSubConnection,
    ResourceManagerConnection,
    SearchConnection,
    StorageConnection
)

credentials = gcloud.credentials.get_credentials()

bigquery_connection = BigQueryConnection(credentials=credentials)
datastore_connection = DatastoreConnection(credentials=credentials)
dns_connection = DNSConnection(credentials=credentials)
pubsub_connection = PubSubConnection(credentials=credentials)
resource_manager_connection = ResourceManagerConnection(credentials=credentials)
search_connection = SearchConnection(credentials=credentials)
storage_connection = StorageConnection(credentials=credentials)
