from gcloud import datastore
from gcloud_requests import connection

from threading import Thread


client = datastore.Client(connection=connection.connection)


def r():
    forms = datastore.Query(client, "Form").fetch()
    for form in forms:
        print form
        datastore.put(form)


threads = []
for i in range(100):
    t = Thread(target=r)
    t.start()
    threads.append(t)

for t in threads:
    t.join()
