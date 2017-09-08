import logging
import time

from datetime import datetime
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request as AuthRequest
from requests import Session
from threading import Thread


#: The number of seconds to wait between refresh attempts.
DEFAULT_WAIT_TIME = 60


class CredentialsWatcher(Thread):
    """Watches a Credentials object in a background thread,
    periodically refreshing it.

    Parameters:
      credentials(Credentials)
    """

    def __init__(self, credentials):
        super(CredentialsWatcher, self).__init__()
        self.setDaemon(True)
        self.credentials = credentials
        self.session = session = Session()
        self.request = AuthRequest(session)
        self.logger = logging.getLogger("CredentialsWatcher[{}]".format(id(credentials)))
        self.start()

    def run(self):
        while True:
            self.logger.debug("Ticking...")
            wait_time = self.tick()

            self.logger.debug("Sleeping for %.02f...", wait_time)
            time.sleep(wait_time)

    def tick(self):
        if not self.credentials.valid:
            try:
                self.logger.debug("Refreshing credentials...")
                self.credentials.refresh(self.request)
            except RefreshError:
                self.warning("Failed to refresh credentials...", exc_info=True)

        if self.credentials.expiry:
            # We don't need to skew this value backward because of
            # https://github.com/GoogleCloudPlatform/google-auth-library-python/blob/9281ca026019869bc5fb10ee288a5cd9e837808f/google/auth/credentials.py#L62
            return (self.credentials.expiry - datetime.utcnow()).total_seconds()
        return DEFAULT_WAIT_TIME
