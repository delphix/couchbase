#!/bin/bash

#this script creates a virtual environment and install the below packages:
#dvp==1.0.0
#pytest==4.6.10
#pytest-cov
#pytest-html
DEFAULT_ENV_NAME="env"

printMessage(){
    echo "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
    echo "$1"
    echo ""
}

if [[ "$1" == "-h" ]]; then
  printMessage ""
  echo "Usage: `basename $0` [Provide the virtual environment to create. For example: ./virtualEnvSetup.sh 'CouchbaseSetup']"
  echo "        Default environment name is: $DEFAULT_ENV_NAME"
  echo "        List of python libraries which will be installed in this set up: dvp, pytest, pytest-cov, pytest-html"
  printMessage ""
  exit 0
fi

env_name=$1
if [[ "$env_name" == "" ]] ; then
    env_name=${DEFAULT_ENV_NAME}
    printMessage "Setting default virtual environment name as: $env_name"
fi

ROOT_DIR=$PWD/test
VIRTUAL_ENV_PATH="${ROOT_DIR}"/${env_name}
if [[ -d ${VIRTUAL_ENV_PATH} ]] ; then
    printMessage "${VIRTUAL_ENV_PATH} exist, please provide different name"
    exit 0
fi

printMessage "Virtual environment name is : $env_name, Path: $ROOT_DIR"

virtualenv -p python2.7 ${VIRTUAL_ENV_PATH}
if [[ $? -ne 0 ]]; then
    rm -rf ${VIRTUAL_ENV_PATH}
    printMessage "Virtual environment creation failed, removed ${VIRTUAL_ENV_PATH}"
    exit 1
fi

. "${VIRTUAL_ENV_PATH}"/bin/activate
if [[ $? -ne 0 ]]; then
    rm -rf ${VIRTUAL_ENV_PATH}
    printMessage "Virtual environment activation failed, removed ${VIRTUAL_ENV_PATH}"
    exit 1
fi


pip install -r "${ROOT_DIR}"/requirements.txt
if [[ $? -ne 0 ]]; then
    deactivate
    rm -rf ${VIRTUAL_ENV_PATH}
    printMessage "Package installation failed, removed ${VIRTUAL_ENV_PATH}"
    exit 1
fi

printMessage "Set up completed in virtual environment ${VIRTUAL_ENV_FOLDER}"
deactivate
printMessage "Deactivated the environment. Execute: . test/${env_name}/bin/activate to activate again"
printMessage "To delete this setup, execute: rm -rf test/$env_name"
