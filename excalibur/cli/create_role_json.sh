#!/usr/bin/env bash

if [[ $# != 2 ]];
then
  echo ""
  echo "Enter Role Name and Application name/s e.g"
  echo "  $0 Internet-Browsing firefox"
  echo ""
  echo "If there is more than 1 application then list the names comma separated and in quotes preceeded with backslash (\) e.g:"
  echo "  $0 Banking \"firefox\\\",\\\"wincmd\""
  echo ""
  exit 0
fi

echo -e '{
    "name": '\"$3\"',
    "version": "1.0",
    "applicationIds": ['\"$4\"'],
    "startingResourceIds": [],
    "startingTransducerIds": ["path_mkdir", "bprm_set_creds", "task_create", "task_alloc", "inode_create", "socket_connect", "socket_bind", "socket_accept", "socket_listen", "create_process", "process_start", "process_died", "srv_create_proc", "open_fd"]
}' > role_$3.json

echo ""
echo "#################################"
echo "Created <role_$3.json> file"
echo "#################################"
echo ""
cat role_$3.json
