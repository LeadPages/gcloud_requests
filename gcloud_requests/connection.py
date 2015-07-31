import gcloud.credentials

from .requests_connection import DatastoreConnection, JSONConnection

credentials = gcloud.credentials.get_credentials()
datastore_connection = DatastoreConnection(credentials=credentials)
json_connection = JSONConnection(credentials=credentials)
