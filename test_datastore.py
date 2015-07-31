import time

from gcloud import datastore
from gcloud_requests import connection

from threading import Thread


client = datastore.Client(connection=connection.requests_connection)
ns = "gcloud-requests-{}".format(time.time())

for i in range(10):
    e = datastore.Entity(key=client.key("Form", namespace=ns))
    e.update(x=i)
    client.put(e)


def r():
    forms = client.query(kind="Form", namespace=ns).fetch()
    for form in forms:
        print form
        client.put(form)


threads = []
for i in range(100):
    t = Thread(target=r)
    t.start()
    threads.append(t)

for t in threads:
    t.join()
