#!/usr/bin/env bash

if [[ $# != 1 ]];
then
  echo ""
  echo "Enter Role name e.g:"
  echo "  $0 windowscmd1544341006"
  echo ""
  exit 0
fi

cd ../excalibur/cli

python3 sso_login.py -u jmitchell@virtue.com -p Test123! -A APP_1 excalibur.galahad.com:5002

export VIRTUE_ADDRESS="excalibur.galahad.com"
export VIRTUE_TOKEN=$(cat usertoken.json)

python3 virtue-admin user role authorize --username=jmitchell --roleId=$1

#virtueId=$(python3 virtue-admin virtue create --username=jmitchell --roleId=$1 |grep id |cut -d'"' -f 4)
#echo "The Virtue ID is --> $virtueId"
#echo ""

python3 virtue-admin virtue create --username=jmitchell --roleId=$1

echo "Run the following command once virtue is created:"
echo "cd ~/galahad/excalibur/cli;python3 virtue virtue launch --virtueId=<VIRTUE_ID>;cd -"

#python3 virtue virtue launch --virtueId=$virtueId
