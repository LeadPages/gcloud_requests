# gcloud_requests

[![GitHub license](https://img.shields.io/github/license/leadpages/gcloud_requests.svg?style=flat-square)](https://raw.githubusercontent.com/leadpages/gcloud_requests/master/LICENSE)
[![PyPI Version](https://img.shields.io/pypi/v/gcloud_requests.svg?style=flat-square)](https://pypi.python.org/pypi/gcloud_requests/)
[![Build Status](https://img.shields.io/travis/LeadPages/gcloud_requests.svg?style=flat-square)](https://travis-ci.org/LeadPages/gcloud_requests)
[![Code Climate](https://img.shields.io/codeclimate/github/LeadPages/gcloud_requests.svg?style=flat-square)](https://codeclimate.com/github/LeadPages/gcloud_requests)
[![PyPI Popularity](https://img.shields.io/pypi/dm/gcloud_requests.svg?style=flat-square)](https://pypi.python.org/pypi/gcloud_requests/)

Thread-safe client functionality for gcloud-python via requests.

## Installation

```bash
pip install --upgrade gcloud_requests
```

**Note** that at this time, only `gcloud==0.18.1` on Python 2.7 is
officially supported.

## Usage

The library provides new HTTP objects that can be passed in to the
`gcloud.*.Client` constructors (per supported API module). For example,
to use the connection class (with proper retrying implemented) for
Google Cloud Datastore:

```python
from gcloud import datastore
from gcloud_requests.connection import datastore_http

client = datastore.Client(http=datastore_http)
client.query(kind="EntityKind").fetch()
```

and for the Google Cloud Storage service:

```python
from gcloud import storage
from gcloud_requests.connection import storage_http

client = storage.Client(http=storage_http, project="my-project")
bucket = client.get_bucket("my-bucket")
```

## Custom credentials

Using a custom HTTP object causes gcloud Clients to ignore whatever
Credentials objects you pass into them manually. If you need to use a
custom set of credentials with `gcloud_requests` you must instantiate
a `RequestsProxy` object by passing in those credentials and then
passing that instance to your client like so:

``` python
from gcloud import datastore
from gcloud_requests.requests_connection import DatastoreRequestsProxy

http = DatastoreRequestsProxy(custom_credentials)
client = datastore.Client(http=http)
```

## Background

The [gcloud-python][gcloud-python] library for accessing Google Cloud
Platform services like Google Cloud Datastore, Google Cloud Storage,
Google BigQuery, and others, relies on the `httplib2` library to handle
the underlying Protobuf requests. This library (`httplib2`) is not
threadsafe.

Based on notes in [gcloud-python#926][issue-926], [gcloud-python#908][issue-908],
and [gcloud-python#1214][issue-1214], this library replaces the
underlying transport with [`requests`][requests].

## Running Tests

It's strongly encouraged that you **let Travis run the tests**. This is
because running the tests requires `gcd`, the Google Cloud Datastore
tools, which also requires a Google Cloud Platform service key...if
you're still intrigued, work through the [`gcd documentation`][gcd] and
then simply install `pytest` and run the tests with `py.test`.

## Authors

`gcloud_requests` was authored at [Leadpages][leadpages]. You can
find out more about contributors [here][contributors]. We welcome
contributions, and [we're always looking][careers] for more
engineering talent!

## Contributing

Please read [our contributor's guide](./CONTRIBUTING.md).

[leadpages]: http://leadpages.net
[careers]: http://www.leadpages.net/careers
[contributors]: https://github.com/leadpages/gcloud_requests/graphs/contributors
[gcd]: https://cloud.google.com/datastore/docs/tools/
[gcloud-python]: https://github.com/GoogleCloudPlatform/gcloud-python
[requests]: http://python-requests.org
[issue-908]: https://github.com/GoogleCloudPlatform/gcloud-python/issues/908
[issue-926]: https://github.com/GoogleCloudPlatform/gcloud-python/issues/926
[issue-1214]: https://github.com/GoogleCloudPlatform/gcloud-python/issues/1214
