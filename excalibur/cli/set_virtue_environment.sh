#!/usr/bin/env bash

(return 2>/dev/null) && sourced=1 || sourced=0

if [[ $sourced == 0 ]];
then
  echo ""
  echo "Error: Script has not been sourced."
  echo "Please source the script to set the environment variables e.g:"
  echo "  source ${BASH_SOURCE/.\//} <username> <password>"
  echo ""
  echo ""
else
  if [[ $# != 2 ]];
  then
    echo ""
    echo "Enter username and passwurd e.g"
    echo "  $BASH_SOURCE jmitchell@virtue.gov Test123!"
    echo ""
    echo ""
  else
    python3 sso_login.py -u $1 -p $2 -A APP_1 excalibur.galahad.com:5002

    export VIRTUE_ADDRESS="excalibur.galahad.com"
    export VIRTUE_TOKEN=$(cat usertoken.json)
  fi
fi