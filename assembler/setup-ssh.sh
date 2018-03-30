#!/bin/bash
ssh -i stage1/id_rsa -p 5555 -o BatchMode=yes -o StrictHostKeyChecking=no -o "UserKnownHostsFile /dev/null" -N -L 6767:127.0.0.1:6767 virtue@localhost &
sleep 1 
ssh -i stage1/id_rsa -p 6767 -N -L 10000:127.0.0.1:2023 virtue@localhost

