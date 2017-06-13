from .proxy import RequestsProxy  # noqa
from .datastore import DatastoreRequestsProxy, enter_transaction, exit_transaction  # noqa
from .storage import CloudStorageRequestsProxy  # noqa

__version__ = "1.0.3"
