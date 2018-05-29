#!/bin/bash

# Setup LDAP from scratch and install all pertinent data for Testing
BASE_DIR="galahad/tests"
LDAP_SCRIPTS_DIR="ldap"

# Cleanup any old LDAP setup
sudo apt-get purge slapd ldap-utils -y
sudo rm -fr /etc/ldap
#
sudo $HOME/$BASE_DIR/$LDAP_SCRIPTS_DIR/install_ldap.sh
$HOME/$BASE_DIR/$LDAP_SCRIPTS_DIR/add_canvas_schema.sh
$HOME/$BASE_DIR/$LDAP_SCRIPTS_DIR/create_base_ldap_structure.py
