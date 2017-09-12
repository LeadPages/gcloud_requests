import logging
import time

from datetime import datetime, timedelta
from gcloud_requests import CredentialsWatcher
from google.auth.exceptions import RefreshError


logging.basicConfig(level=10)


class StubCredentials(object):
    def __init__(self, refresh_every=3600):
        self.refresh_calls = 0
        self.refresh_every = refresh_every
        self.expiry = None

    def refresh(self, request):
        self.refresh_calls += 1
        self.expiry = datetime.utcnow() + timedelta(seconds=self.refresh_every)

    @property
    def valid(self):
        return self.expiry and not self.expired

    @property
    def expired(self):
        return (datetime.utcnow() - self.expiry).total_seconds() > 0


class FailingCredentials(StubCredentials):
    def refresh(self, request):
        raise RefreshError("refresh failed")


class BrokenCredentials(StubCredentials):
    def __init__(self, refresh_every=3600):
        super(BrokenCredentials, self).__init__(refresh_every)
        self.expiry = time.time()

    @property
    def valid(self):
        return True

    def refresh(self, request):
        raise RuntimeError("some coding error")


def test_credentials_watcher_refresh_calls_credentials_every_tick():
    # Given that I have a credentials watcher
    watcher = CredentialsWatcher()

    # And a stub credentials object that needs to be refreshed every second
    credentials = StubCredentials(refresh_every=1)

    # If I watch that object
    watcher.watch(credentials)

    # And sleep for 3 seconds
    time.sleep(3)

    # I expect the credentials to have been refreshed 3 or 4 times
    assert credentials.refresh_calls in (3, 4)


def test_credentials_watcher_refresh_calls_many_credentials_at_once():
    # Given that I have a credentials watcher
    watcher = CredentialsWatcher()

    # And a couple stub credentials objects at different refresh rates
    credentials_1 = StubCredentials(refresh_every=1)
    credentials_2 = StubCredentials(refresh_every=5)

    # If I watch those objects
    watcher.watch(credentials_1)
    watcher.watch(credentials_2)

    # And sleep for 5 seconds
    time.sleep(5)

    # I expect the first one to have been refreshed 5 or 6 times
    assert credentials_1.refresh_calls in (5, 6)
    # And the second to have been refreshed at least once
    assert credentials_2.refresh_calls in (1, 2)


def test_credentials_watcher_is_resilient_to_refresh_errors():
    # Given that I have a credentials watcher
    watcher = CredentialsWatcher()

    # And a couple of credentials objects
    # One that always refreshes successfully
    credentials_1 = StubCredentials(refresh_every=1)
    # And one that always fails
    credentials_2 = FailingCredentials()

    # If I watch those objects
    watcher.watch(credentials_1)
    watcher.watch(credentials_2)

    # And sleep for 5 seconds
    time.sleep(5)

    # I expect the first one to have been refreshed 5 or 6 times
    assert credentials_1.refresh_calls in (5, 6)
    # And the second to never have been refreshed
    assert credentials_2.refresh_calls == 0


def test_credentials_watcher_is_resilient_to_coding_errors():
    # Given that I have a credentials watcher
    watcher = CredentialsWatcher()

    # And a couple of credentials objects
    # One that always refreshes successfully
    credentials_1 = StubCredentials(refresh_every=1)
    # And one that always fails due to a coding error
    credentials_2 = BrokenCredentials()

    # If I watch those objects
    watcher.watch(credentials_1)
    watcher.watch(credentials_2)

    # And sleep for 5 seconds
    time.sleep(5)

    # I expect the first one to have been refreshed 5 or 6 times
    assert credentials_1.refresh_calls in (5, 6)
    # And the second to never have been refreshed
    assert credentials_2.refresh_calls == 0
    # And the second to have been removed from the watch list
    assert credentials_2 not in watcher.watch_list


def test_credentials_watcher_can_be_stopped():
    # Given that I have a credentials watcher
    watcher = CredentialsWatcher()

    # And a stub credentials object that needs to be refreshed once an hour
    credentials = StubCredentials(refresh_every=3600)

    # If I watch that object
    watcher.watch(credentials)

    # Then stop the watcher
    watcher.stop()

    # I expect it to stop
    assert not watcher.running
