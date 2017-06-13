# gcloud_requests

[![GitHub license](https://img.shields.io/github/license/leadpages/gcloud_requests.svg?style=flat-square)](https://raw.githubusercontent.com/leadpages/gcloud_requests/master/LICENSE)
[![PyPI Version](https://img.shields.io/pypi/v/gcloud_requests.svg?style=flat-square)](https://pypi.python.org/pypi/gcloud_requests/)
[![Build Status](https://img.shields.io/travis/LeadPages/gcloud_requests.svg?style=flat-square)](https://travis-ci.org/LeadPages/gcloud_requests)
[![Code Climate](https://img.shields.io/codeclimate/github/LeadPages/gcloud_requests.svg?style=flat-square)](https://codeclimate.com/github/LeadPages/gcloud_requests)
[![PyPI Popularity](https://img.shields.io/pypi/dm/gcloud-requests.svg?style=flat-square)](https://pypi.python.org/pypi/gcloud_requests/)

Thread-safe client functionality for `google-cloud-{datastore,storage}` via requests.

## Installation

```bash
pip install --upgrade gcloud_requests
```

**Note** that at this time, only `google-cloud-datastore==1.0.0` is
officially supported.

## Usage

Google Cloud Datastore:

```python
from google.cloud import datastore
from gcloud_requests import DatastoreRequestsProxy

client = datastore.Client(_http=DatastoreRequestsProxy(), _use_grpc=False)
client.query(kind="EntityKind").fetch()
```

Google Cloud Storage:

```python
from google.cloud import storage
from gcloud_requests import DatastoreRequestsProxy

proxy = CloudStorageRequestsProxy()
client = storage.Client(credentials=proxy.credentials, _http=proxy)
bucket = client.get_bucket("my-bucket")
```

## Running Tests

1. Install the dev deps with `pip install -r requirements-dev.txt`
1. then run `py.test`.

*Note*: This will run the tests against whatever GCP project you're
currently logged into via the gcloud tool.

## Authors

`gcloud_requests` was authored at [Leadpages][leadpages].  You can
find out more about contributors [here][contributors].  We welcome
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
