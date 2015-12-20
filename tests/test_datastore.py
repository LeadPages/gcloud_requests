import logging
import multiprocessing
import time

from gcloud import datastore
from gcloud_requests.connection import datastore_connection

from threading import Thread

logging.basicConfig(level=logging.DEBUG)

client = datastore.Client(http=datastore_connection.http)
ns = "gcloud-requests-{}".format(time.time())

forms = client.query(kind="Form", namespace=ns).fetch()
for form in forms:
    client.delete(form.key)

for i in range(100):
    e = datastore.Entity(key=client.key("Form", namespace=ns))
    e.update(x=i)
    client.put(e)


def r():
    forms = client.query(kind="Form", namespace=ns).fetch()
    for form in forms:
        logging.info(str(form))
        client.put(form)


threads = []
for i in range(multiprocessing.cpu_count()):
    t = Thread(target=r)
    t.start()
    threads.append(t)

for t in threads:
    t.join()
