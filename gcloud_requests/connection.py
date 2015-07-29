import gcloud.credentials
import gcloud.datastore

# Re-export everything from gcloud.datastore.
from gcloud.datastore import *  # noqa

from .requests_connection import DatastoreConnection

credentials = gcloud.credentials.get_credentials()
requests_connection = DatastoreConnection(credentials=credentials)
