import pytest

from gcloud_requests import CloudStorageRequestsProxy, DatastoreRequestsProxy, PubSubRequestsProxy


@pytest.fixture(scope="session")
def datastore_proxy():
    return DatastoreRequestsProxy()


@pytest.fixture(scope="session")
def pubsub_proxy():
    return PubSubRequestsProxy()


@pytest.fixture(scope="session")
def storage_proxy():
    return CloudStorageRequestsProxy()
