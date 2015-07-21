from gcloud_requests import datastore

from threading import Thread


def r():
    forms = datastore.Query("Form").fetch()
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
