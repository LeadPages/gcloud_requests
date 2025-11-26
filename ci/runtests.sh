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
  # copy, don't link, because we changeit with `sed`
  cp -v /workspace/requirements.txt     /app/requirements.txt
  ln -s /workspace/requirements_dev.txt /app/requirements_dev.txt
  ln -s /workspace/setup.cfg            /app/setup.cfg
  ln -s /workspace/setup.py             /app/setup.py
}

function run_tests() {
  cd /app

  # Runtime with venv -> 3m:23s, without venv -> 2m:43s
  # this is a throwaway container, venv not needed!
  #pip install virtualenv
  #virtualenv .venv
  #. .venv/bin/activate

  export HOME=/root      # this is a cloudbuild problem!!!!

  sed -i requirements.txt -e "s:^six$:six==1.15:"
  ls -la
  cat requirements.txt requirements_dev.txt
  pip install -r requirements_dev.txt
  py.test tests
}

function main() {
  setup_root
  setup_app
  run_tests
}

main $@