from .credentials_watcher import CredentialsWatcher  # noqa
from .proxy import RequestsProxy  # noqa
from .datastore import DatastoreRequestsProxy, enter_transaction, exit_transaction  # noqa
from .pubsub import PubSubRequestsProxy  # noqa
from .storage import CloudStorageRequestsProxy  # noqa

__version__ = "2.0.2"
