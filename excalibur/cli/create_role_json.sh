#!/usr/bin/env bash

if [[ $# != 4 ]];
then
  echo ""
  echo "Enter username, passwurd, Role Name and Application name/s e.g"
  echo "  $0 jmitchell@virtue.gov Test123! Internet-Browsing firefox"
  echo ""
  echo "If there is more than 1 application then list the names comma separated and in quotes preceeded with backslash (\) e.g:"
  echo "  $0 jmitchell@virtue.gov Test123! Banking \"firefox\\\",\\\"wincmd\""
  echo ""
  exit 0
fi

python3 sso_login.py -u $1 -p $2 -A APP_1 excalibur.galahad.com:5002

export VIRTUE_ADDRESS="excalibur.galahad.com"
export VIRTUE_TOKEN=$(cat usertoken.json)

echo -e '{
    "name": '\"$3\"',
    "version": "1.0",
    "applicationIds": ['\"$4\"'],
    "startingResourceIds": [],
    "startingTransducerIds": ["path_mkdir", "bprm_set_creds", "task_create", "task_alloc", "inode_create", "socket_connect", "socket_bind", "socket_accept", "socket_listen", "create_process", "process_start", "process_died", "srv_create_proc", "open_fd"]
}' > role_$3.json

echo "#################################"
echo "Created <role_$3.json> file"
echo "#################################"
cat role_$3.json
