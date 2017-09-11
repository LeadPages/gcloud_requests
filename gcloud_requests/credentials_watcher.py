import logging

from datetime import datetime
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request as AuthRequest
from requests import Session
from threading import Condition, Thread


#: The max number of seconds to wait between refresh attempts.
MAX_WAIT_TIME = 3600


class CredentialsWatcher(Thread):
    """Watches Credentials objects in a background thread,
    periodically refreshing them.
    """

    def __init__(self):
        super(CredentialsWatcher, self).__init__()
        self.setDaemon(True)
        self.watch_list_updated = Condition()
        self.watch_list = []
        self.session = session = Session()
        self.request = AuthRequest(session)
        self.logger = logging.getLogger("gcloud_requests.CredentialsWatcher")
        self.start()

    def run(self):
        with self.watch_list_updated:
            while True:
                self.logger.debug("Ticking...")
                wait_time = self.tick()

                self.logger.debug("Sleeping for %.02f...", wait_time)
                self.watch_list_updated.wait(timeout=wait_time)

    def tick(self):
        wait_time = MAX_WAIT_TIME
        for credentials in self.watch_list:
            try:
                if not credentials.valid:
                    try:
                        self.logger.debug("Refreshing credentials %r...", credentials)
                        credentials.refresh(self.request)
                    except RefreshError:
                        self.logger.warning("Failed to refresh credentials...", exc_info=True)
                    except Exception:
                        self.logger.exception("Unexpected error refreshing credentials %r.", credentials)

                if credentials.expiry:
                    # We don't need to skew this value backward because of
                    # https://github.com/GoogleCloudPlatform/google-auth-library-python/blob/9281ca026019869bc5fb10ee288a5cd9e837808f/google/auth/credentials.py#L62
                    delta = (credentials.expiry - datetime.utcnow()).total_seconds()
                    wait_time = min(wait_time, delta)
            except Exception:
                self.logger.exception("Unexpected error processing credentials %r.", credentials)
                self.watch_list.remove(credentials)
        return wait_time

    def watch(self, credentials):
        with self.watch_list_updated:
            self.watch_list.append(credentials)
            self.watch_list_updated.notify()

    def unwatch(self, credentials):
        with self.watch_list_updated:
            self.watch_list.remove(credentials)
            self.watch_list_updated.notify()
