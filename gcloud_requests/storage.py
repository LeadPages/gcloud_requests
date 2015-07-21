import gcloud.credentials
import gcloud.storage

# Re-export everything from gcloud.storage.
from gcloud.storage import *  # noqa

from .requests_connection import StorageConnection

credentials = gcloud.credentials.get_credentials()
connection = StorageConnection(credentials=credentials)
gcloud.storage.set_default_connection(connection)
