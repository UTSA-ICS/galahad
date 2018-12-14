#!/usr/bin/env bash

if [[ $# != 2 ]];
then
  echo ""
  echo "Enter Application name and unity size e.g"
  echo "  $0 firefox 4GB"
  echo ""
  exit 0
fi

cd ../excalibur/cli

python3 sso_login.py -u jmitchell@virtue.com -p Test123! -A APP_1 excalibur.galahad.com:5002

export VIRTUE_ADDRESS="excalibur.galahad.com"
export VIRTUE_TOKEN=$(cat usertoken.json)

echo -e '{
    "name": '\"$1\"',
    "version": "1.0",
    "applicationIds": ['\"$1\"'],
    "startingResourceIds": [],
    "startingTransducerIds": []
}' > role.json

python3 virtue-admin role create --role=role.json --unitySize=$2