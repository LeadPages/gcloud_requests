#!/bin/sh

function setup_root() {
  mkdir /root/.pip && ln -s /workspace/pip.conf /root/.pip/pip.conf
  ln -s /workspace/netrc                 /root/.netrc
  ln -s /workspace/cloudbuild_pypirc     /root/.pypirc
}

function setup_app() {
  mkdir /app && cd /app
  # copy, because we wanna be able to toss out __pychache__ and *.pyc files
  cp -ar /workspace/gcloud_requests      /app/gcloud_requests
  cp -ar /workspace/tests                /app/tests
  # copy, don't link, because we change it with `sed`
  cp -v /workspace/requirements.txt     /app/requirements.txt
  ln -s /workspace/requirements-dev.txt /app/requirements-dev.txt
  ln -s /workspace/setup.cfg            /app/setup.cfg
  ln -s /workspace/setup.py             /app/setup.py
}

function build_wheel() {
  cd /app
  export HOME=/root      # Damn you cloudbuild, presets to /home/builder/home ...
  sed -i requirements.txt -e "s:^six$:six==1.15:"
  pip install -r requirements.txt
  pip install wheel

  python setup.py bdist_wheel

  ls -la build
  ls -la dist
  ls -la .
}

function upload_lib() {
  # twine needs a compiler
  cd /app
  apk update && apk upgrade && apk add build-base libffi-dev
  pip install twine
  # "local" refers to the [local] section in pypirc which specifies the URL
  echo "Uplaod library to Artifactory"
  twine upload \
    --repository local \
    dist/* \
    --config-file /root/.pypirc
}

function main() {
  setup_root
  setup_app
  build_wheel
  # additional safegard against uploading
  if [ x"${BUILD_TYPE}" == x"release" ]; then
    upload_lib
  elif [ x"${BUILD_TYPE}" == x"local" ]; then
    echo " copy into /workspace dir, which is a docker volume mount"
    rm -rf  /workspace/{build,dist}
    cp -avr /app/build /app/dist /workspace/
  else
    echo "Discard builded library!"
  fi
}

main $@