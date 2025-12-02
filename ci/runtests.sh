#!/bin/sh

set -e

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
  ln -s /workspace/requirements-dev.txt /app/requirements-dev.txt
  ln -s /workspace/setup.cfg            /app/setup.cfg
  ln -s /workspace/setup.py             /app/setup.py
}

function setup_env() {
  cd /app
  # this is a throwaway container, venv not needed!

  ls -la
  cat requirements.txt requirements-dev.txt
  pip install -r requirements-dev.txt
}

function main() {
  local onlysetup=$1
  export HOME=/root      # this is a cloudbuild problem!!!!
  setup_root
  setup_app
  setup_env
  if [ x"${onlysetup}" != x"onlysetup" ]; then
    echo "RUNNING TESTS: onlysetup=<${onlysetup}>"
    py.test -sv tests
  else
    echo "ONLY PREPARE ENV: onlysetup=<${onlysetup}>"
  fi
}

main $@