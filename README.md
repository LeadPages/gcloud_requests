# gcloud_requests

[![GitHub license](https://img.shields.io/github/license/leadpages/gcloud_requests.svg)](https://raw.githubusercontent.com/leadpages/gcloud_requests/master/LICENSE)
[![PyPI Version](https://img.shields.io/pypi/v/gcloud_requests.svg)](https://pypi.python.org/pypi/gcloud_requests/)
[![Build Status](https://img.shields.io/travis/LeadPages/gcloud_requests.svg)](https://travis-ci.org/LeadPages/gcloud_requests)
[![Code Climate](https://img.shields.io/codeclimate/github/LeadPages/gcloud_requests.svg)](https://codeclimate.com/github/LeadPages/gcloud_requests)

Thread-safe client functionality for `google-cloud-{datastore,storage}` via requests.

## Installation

```bash
pip install --upgrade gcloud_requests
```

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
from gcloud_requests import CloudStorageRequestsProxy

proxy = CloudStorageRequestsProxy()
client = storage.Client(credentials=proxy.credentials, _http=proxy)
bucket = client.get_bucket("my-bucket")
```

## Running Tests

1. Install the dev deps with `pip install -r requirements-dev.txt`
1. then run `py.test`.

*Note*: This will run the tests against whatever GCP project you're
currently logged into via the gcloud tool.

# Running comprehensive tests

req is a library that is released for multiple versions of python. When
build in CI we run the tests against every version of python the library is
supposed to work with.  This can be simulated in development by running the
the tests inside docker containers.  The process is simplified by just
running `make ci-tests`.  If you wanna run a test suite locally against a
specific version of python only you can run `make PY_VERSION=3.11 test`.

*Note*: This will run the tests against whatever GCP project `lp-infra-lab`.

# Adding new python versions to supported roaster

If you would like to add a new version of Python to the supported versions
it must be handled in three locations:
1. For local changes the variable `SUPPORTED_PY_VERSIONS' in the Makefile
   must be adjusted to include (or exclude) the versions in question.
2. in `ci/cloudbuild.yaml` steps need to be added (or removed) to address
   the different versions of Python as well.
3. in `ci/cloudbuild.yaml`, update the `_LATEST_SUPPORTED_PY_VERSION` to the 
   latest supporeted python version.

# Building a Pre-Release version

Running `make bdist_wheel` will build the library instide a container and
copy the results into `./build/` and `./dist/`.  It will not actually
publish the wheel
To Publish the wheel from the local setup, run `make BUILD_TYPE=release bdist_wheel`

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
