#!/usr/bin/env bash

if [[ $# != 3 ]];
then
  echo ""
  echo "Enter Username, password and migration_interval time in seconds"
  echo "  $0 jmitchell@virtue.gov Test123! 300"
  echo ""
  echo ""
  exit 0
fi

CLI_HOME="galahad/excalibur/cli"

cd $HOME/$CLI_HOME

python3 sso_login.py -u $1 -p $2 -A APP_1 excalibur.galahad.com:5002

export VIRTUE_ADDRESS="excalibur.galahad.com"
export VIRTUE_TOKEN=$(cat usertoken.json)

python3 virtue-admin auto migrate start --migration_interval=$3
