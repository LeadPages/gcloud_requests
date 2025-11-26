DOCKER != which docker
MKDIR != which mkdir
RM != which rm

PROJECT=gcloud-requests

LATEST_SUPPORTED_PY_VERSION=3.11

SUPPORTED_PY_VERSIONS=2.7 3.6 3.7 3.8 3.9 $(LATEST_SUPPORTED_PY_VERSION)

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
	$(DOCKER) run -it --rm=true --name=$(PROJECT)_python$(PY_VERSION) \
	  -v $(CURDIR):/workspace \
	  -v ${HOME}/.config/gcloud:/root/.config/gcloud:ro \
	  -e GOOGLE_APPLICATION_CREDENTIALS=/root/.config/gcloud/application_default_credentials.json \
	  python:$(PY_VERSION)-alpine \
	  /bin/sh -c "/workspace/ci/runtests.sh onlysetup; exec /bin/sh"

test: netrc pip.conf cloudbuild_pypirc ${HOME}/.config/gcloud/application_default_credentials.json
	$(DOCKER) run -it --rm=true --name=$(PROJECT)_$@ \
	  -v $(CURDIR):/workspace \
	  -v ${HOME}/.config/gcloud:/root/.config/gcloud:ro \
	  -e GOOGLE_APPLICATION_CREDENTIALS=/root/.config/gcloud/application_default_credentials.json \
	  python:$(PY_VERSION)-alpine sh /workspace/ci/runtests.sh

ci-tests:
	$(foreach pyversion, $(SUPPORTED_PY_VERSIONS), $(MAKE) PY_VERSION=$(pyversion) test;)

bdist_wheel: netrc pip.conf cloudbuild_pypirc ${HOME}/.config/gcloud/application_default_credentials.json
	# THIS WILL PUBLISH THE LIBRARY! HAVE YOU SET THE gcloud_requests/__init__.py versions TO A DEV VERSION???
	@if [ x"$(BUILD_TYPE)" == x"release" ]; then \
	  if grep __version__ gcloud_requests/__init__.py | grep -q '[0-9]*\.[0-9]*[\.\-]dev'; then \
	    $(DOCKER) run -it --rm=true --name=$(PROJECT)_$@ \
	      -v $(CURDIR):/workspace \
		  -v ${HOME}/.config/gcloud:/root/.config/gcloud:ro \
		  -e GOOGLE_APPLICATION_CREDENTIALS=/root/.config/gcloud/application_default_credentials.json \
	      --env BUILD_TYPE=$(BUILD_TYPE) \
	      python:$(LATEST_SUPPORTED_PY_VERSION)-alpine /bin/sh /workspace/ci/buildwheel.sh; \
	  else \
	    echo "The __version__ in gcloud_requests/__init__.py does not contain  'dev' designator"; \
	  fi \
	else \
	  $(DOCKER) run -it --rm=true --name=$(PROJECT)_$@ \
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