import logging
import multiprocessing
import pytest
import time

from concurrent.futures import ThreadPoolExecutor
from google.cloud import datastore
from gcloud_requests import DatastoreRequestsProxy
from six.moves import xrange

logging.basicConfig(level=logging.INFO)

ns = "gcloud-requests-{}".format(time.time())
client = datastore.Client(_http=DatastoreRequestsProxy(), _use_grpc=False)
workers = multiprocessing.cpu_count() * 2


@pytest.fixture
def forms():
    logging.info("Populating dataset...")

    def create(i):
        e = datastore.Entity(key=client.key("Form", namespace=ns))
        e.update(x=i)
        client.put(e)
        return e.key

    with ThreadPoolExecutor(max_workers=workers) as e:
        keys = list(e.map(create, xrange(250)))

    logging.info("Yielding fixture...")
    yield

    logging.info("Cleaning up...")
    with ThreadPoolExecutor(max_workers=workers) as e:
        list(e.map(client.delete, keys))


def test_datastore_concurrency(forms):
    def thrash(thread_id):
        logging.info("Thrashing in thread %r.", thread_id)
        for form in client.query(kind="Form", namespace=ns).fetch():
            client.put(form)

    with ThreadPoolExecutor(max_workers=workers) as e:
        list(e.map(thrash, xrange(workers)))
