import gcloud.credentials

from .requests_connection import DatastoreConnection, StorageConnection

credentials = gcloud.credentials.get_credentials()
datastore_connection = DatastoreConnection(credentials=credentials)
storage_connection = StorageConnection(credentials=credentials)
