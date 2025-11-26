DOCKER != which docker
MKDIR != which mkdir
RM != which rm

PROJECT=gcloud_requests

SUPPORTED_PY_VERSIONS=2.7 3.6 3.7 3.8 3.9 3.11

.PHONY: test ci-tests

netrc:
	cp ${HOME}/.netrc netrc

pip.conf:
	cp ${HOME}/.pip/pip.conf pip.conf

cloudbuild_pypirc:
	cp ${HOME}/.pypirc cloudbuild_pypirc

gcloud:
	cp ${HOME}/.config/gcloud gcloud

test: netrc pip.conf cloudbuild_pypirc gcloud
	$(DOCKER) run -it --rm=true --name=$(PROJECT)_$@ \
	  -v $(CURDIR):/workspace \
	  python:$(PY_VERSION)-alpine sh /workspace/ci/runtests.sh

ci-tests:
	$(foreach pyversion, $(SUPPORTED_PY_VERSIONS), $(MAKE) PY_VERSION=$(pyversion) test;)

bdist_wheel: netrc pip.conf cloudbuild_pypirc gcloud
	# THIS WILL PUBLISH THE LIBRARY! HAVE YOU SET THE gcloud_requests/__init__.py versions TO A DEV VERSION???
	@if [ x"$(BUILD_TYPE)" == x"release" ]; then \
	  if grep __version__ gcloud_requests/__init__.py | grep -q '[0-9]*\.[0-9]*[\.\-]dev'; then \
	    $(DOCKER) run -it --rm=true --name=$(PROJECT)_$@ \
	      -v $(CURDIR):/workspace \
	      --env BUILD_TYPE=$(BUILD_TYPE) \
	      python:3.11-alpine /bin/sh /workspace/ci/buildwheel.sh; \
	  else \
	    echo "The __version__ in gcloud_requests/__init__.py does not contain  'dev' designator"; \
	  fi \
	else \
	  $(DOCKER) run -it --rm=true --name=$(PROJECT)_$@ \
	    -v $(CURDIR):/workspace \
	    --env BUILD_TYPE=local \
	    python:3.11-alpine /bin/sh /workspace/ci/buildwheel.sh; \
	fi

clean:
	-$(RM) netrc
	-$(RM) pip.conf
	-$(RM) cloudbuild_pypirc
	-$(RM) -rf build
	-$(RM) -rf  dist