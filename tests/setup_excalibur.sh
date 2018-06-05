#!/bin/bash

# Install everything required for testing, except the openldap server
BASE_DIR="galahad/tests"

sudo apt-get update
# Cannot yet automate responses to three-way merge prompts
#sudo apt-get upgrade -y
sudo apt-get install -y python-pip libldap2-dev libsasl2-dev python-logilab-common
sudo apt-get autoremove -y
sudo pip install --upgrade -r $HOME/$BASE_DIR/requirements.txt
