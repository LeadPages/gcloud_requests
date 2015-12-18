# gcloud_requests

[![GitHub license](https://img.shields.io/github/license/LeadPages/gcloud_requests.svg?style=flat-square)](https://raw.githubusercontent.com/LeadPages/gcloud_requests/master/LICENSE)
[![PyPI Version](https://img.shields.io/pypi/v/gcloud_requests.svg?style=flat-square)](https://pypi.python.org/pypi/gcloud_requests/)
[![Build Status](https://img.shields.io/travis/LeadPages/gcloud_requests.svg?style=flat-square)](https://travis-ci.org/LeadPages/gcloud_requests)
[![Code Climate](https://img.shields.io/codeclimate/github/LeadPages/gcloud_requests.svg?style=flat-square)](https://codeclimate.com/github/LeadPages/gcloud_requests)
[![PyPI Popularity](https://img.shields.io/pypi/dm/gcloud_requests.svg?style=flat-square)](https://pypi.python.org/pypi/gcloud_requests/)

Thread-safe client functionality for gcloud-python via requests.

## Installation

```
pip install --upgrade gcloud_requests
```

**Note** that at this time, only `gcloud==0.7.0` on Python 2.7 is
officially supported.

## Usage

The library provides a new connection that can be passed in to the
`gcloud.datastore.Client` constructor.

### Google Cloud Datastore

```
from gcloud import datastore
from gcloud_requests import connection

client = datastore.Client(connection=connection.datastore_connection)
client.query(kind="EntityKind").fetch()
```

### Google Cloud Storage

```
client = gcloud.storage.Client(project="my-project")
client._connection = connection.storage_connection
bucket = client.get_bucket("my-bucket")
```

## Background

The [gcloud-python](https://github.com/GoogleCloudPlatform/gcloud-python)
library for accessing Google Cloud Platform services like Google Cloud
Datastore, Google Cloud Storage, Google BigQuery, and others, relies on
the `httplib2` library to handle the underlying Protobuf requests. This
library (`httplib2`) is not threadsafe.

Based on notes in [gcloud-python#926](https://github.com/GoogleCloudPlatform/gcloud-python/issues/926),
[gcloud-python#908](https://github.com/GoogleCloudPlatform/gcloud-python/issues/908),
and pgcloud-python#1214](https://github.com/GoogleCloudPlatform/gcloud-python/issues/1214),
this library replaces the underlying transport with [`requests`](http://python-requests.org).

## Running Tests

It's strongly encouraged that you **let Travis run the tests**. This is
because running the tests requires `gcd`, the Google Cloud Datastore
tools, which also requires a Google Cloud Platform service key...if
you're still intrigued, work through the [`gcd documentation`](https://cloud.google.com/datastore/docs/tools/)
and then simply install `pytest` and run the tests with `py.test`.

## Authors

`gcloud_requests` was authored at [LeadPages](http://leadpages.net). You
can find out more about contributors [here](https://github.com/LeadPages/gcloud_requests/graphs/contributors)
We welcome contributions, and [we're always looking](http://www.leadpages.net/careers) for more
engineering talent!

## Contributing

Please read [our contributor's guide](./CONTRIBUTING.md).
