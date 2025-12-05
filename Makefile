DOCKER ?= docker
MKDIR ?= mkdir
RM ?= rm

PROJECT=gcloud-requests

LATEST_SUPPORTED_PY_VERSION=3.11

SUPPORTED_PY_VERSIONS=2.7 3.6 3.7 3.8 3.9 $(LATEST_SUPPORTED_PY_VERSION)

# Determine platform flag (only needed for python 2.7)
# grpcio HAS NO PRE_BUILT WHEELS FOR ARM64 FOR PYTHON 2, SO FORCE PLATFORM TO linuc/amd64
# For grpcio We also need to rebuild from source with the alpine image, so for python 2.7, we dont use the full debian
define PLATFORM_ARG
$(if $(filter 2.7,$(PY_VERSION)),--platform=linux/amd64,)
endef
PY_IMAGE = python:$(PY_VERSION)-alpine
ifeq ($(PY_VERSION),2.7)
  PY_IMAGE = python:2.7
endif
# Addtionally, the python 2.7 debian image will need bash to work with runtests.sh and buildwheel.sh
SHELL_CMD = sh
ifeq ($(PY_VERSION),2.7)
  SHELL_CMD = /bin/bash
endif

# NOT FULLY Mocked, setting project ID as lp-infra-lab
GOOGLE_CLOUD_PROJECT ?= lp-infra-lab
DATASTORE_PROJECT_ID ?= $(GOOGLE_CLOUD_PROJECT)
DATASTORE_DATASET    ?= $(GOOGLE_CLOUD_PROJECT)
GCLOUD_PROJECT       ?= $(GOOGLE_CLOUD_PROJECT)

.PHONY: test ci-tests

netrc:
	cp ${HOME}/.netrc netrc

pip.conf:
	cp ${HOME}/.pip/pip.conf pip.conf

cloudbuild_pypirc:
	cp ${HOME}/.pypirc cloudbuild_pypirc

${HOME}/.config/gcloud/application_default_credentials.json:
	gcloud auth application-default login

run: netrc pip.conf cloudbuild_pypirc ${HOME}/.config/gcloud/application_default_credentials.json
	$(DOCKER) run $(PLATFORM_ARG) -it --rm=true --name=$(PROJECT)_python$(PY_VERSION) \
	  -v $(CURDIR):/workspace \
	  -v ${HOME}/.config/gcloud:/root/.config/gcloud:ro \
	  -e GOOGLE_APPLICATION_CREDENTIALS=/root/.config/gcloud/application_default_credentials.json \
	  -e DATASTORE_PROJECT_ID=$(DATASTORE_PROJECT_ID) \
	  -e DATASTORE_DATASET=$(DATASTORE_DATASET) \
	  -e GOOGLE_CLOUD_PROJECT=$(GOOGLE_CLOUD_PROJECT) \
	  -e GCLOUD_PROJECT=$(GCLOUD_PROJECT) \
	  $(PY_IMAGE) \
	  $(SHELL_CMD) -c "/workspace/ci/runtests.sh onlysetup; exec /bin/sh"

lint:
	$(DOCKER) run --rm \
	  -v $(CURDIR):/workspace \
	  python:3.11-alpine sh -c "pip install flake8 && flake8 /workspace/gcloud_requests /workspace/tests"

test: netrc pip.conf cloudbuild_pypirc ${HOME}/.config/gcloud/application_default_credentials.json
	$(DOCKER) run $(PLATFORM_ARG) -it --rm=true --name=$(PROJECT)_$@ \
	  -v $(CURDIR):/workspace \
	  -v ${HOME}/.config/gcloud:/root/.config/gcloud:ro \
	  -e GOOGLE_APPLICATION_CREDENTIALS=/root/.config/gcloud/application_default_credentials.json \
	  -e DATASTORE_PROJECT_ID=$(DATASTORE_PROJECT_ID) \
	  -e DATASTORE_DATASET=$(DATASTORE_DATASET) \
	  -e GOOGLE_CLOUD_PROJECT=$(GOOGLE_CLOUD_PROJECT) \
	  -e GCLOUD_PROJECT=$(GCLOUD_PROJECT) \
	  $(PY_IMAGE) $(SHELL_CMD) /workspace/ci/runtests.sh

ci-tests:
	$(foreach pyversion, $(SUPPORTED_PY_VERSIONS), $(MAKE) PY_VERSION=$(pyversion) test;)

bdist_wheel: netrc pip.conf cloudbuild_pypirc ${HOME}/.config/gcloud/application_default_credentials.json
	# THIS WILL PUBLISH THE LIBRARY! HAVE YOU SET THE gcloud_requests/__init__.py versions TO A DEV VERSION???
	@if [ x"$(BUILD_TYPE)" == x"release" ]; then \
	  if grep __version__ gcloud_requests/__init__.py | grep -q '[0-9]*\.[0-9]*[\.\-]dev'; then \
	    $(DOCKER) run $(PLATFORM_ARG) -it --rm=true --name=$(PROJECT)_$@ \
	      -v $(CURDIR):/workspace \
		  -v ${HOME}/.config/gcloud:/root/.config/gcloud:ro \
		  -e GOOGLE_APPLICATION_CREDENTIALS=/root/.config/gcloud/application_default_credentials.json \
	      --env BUILD_TYPE=$(BUILD_TYPE) \
	      python:$(LATEST_SUPPORTED_PY_VERSION)-alpine /bin/sh /workspace/ci/buildwheel.sh; \
	  else \
	    echo "The __version__ in gcloud_requests/__init__.py does not contain  'dev' designator"; \
	  fi \
	else \
	  $(DOCKER) run $(PLATFORM_ARG) -it --rm=true --name=$(PROJECT)_$@ \
	    -v $(CURDIR):/workspace \
		-v ${HOME}/.config/gcloud:/root/.config/gcloud:ro \
		-e GOOGLE_APPLICATION_CREDENTIALS=/root/.config/gcloud/application_default_credentials.json \
	    --env BUILD_TYPE=local \
	    python:$(LATEST_SUPPORTED_PY_VERSION)-alpine /bin/sh /workspace/ci/buildwheel.sh; \
	fi

clean:
	-$(RM) netrc
	-$(RM) pip.conf
	-$(RM) cloudbuild_pypirc
	-$(RM) -rf build
	-$(RM) -rf  dist