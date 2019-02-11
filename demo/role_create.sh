#!/usr/bin/env bash

if [[ $# != 2 ]];
then
  echo ""
  echo "Enter Role Name, Application name and unity size e.g"
  echo "  $0 Internet-Browsing firefox"
  echo ""
  echo "If there is more than 1 application then list the names comma separated and in quotes preceeded with backslash (\) e.g:"
  echo "  $0 Banking \"firefox\\\",\\\"wincmd\""
  echo ""
  exit 0
fi

cd ../excalibur/cli

python3 sso_login.py -u jmitchell@virtue.gov -p Test123! -A APP_1 excalibur.galahad.com:5002

export VIRTUE_ADDRESS="excalibur.galahad.com"
export VIRTUE_TOKEN=$(cat usertoken.json)

echo -e '{
    "name": '\"$1\"',
    "version": "1.0",
    "applicationIds": ['\"$2\"'],
    "startingResourceIds": [],
    "startingTransducerIds": ["path_mkdir", "bprm_set_creds", "task_create", "task_alloc", "inode_create", "socket_connect", "socket_bind", "socket_accept", "socket_listen", "create_process", "process_start", "process_died", "srv_create_proc", "open_fd"]
}' > role.json

python3 virtue-admin role create --role=role.json

cat role.json
