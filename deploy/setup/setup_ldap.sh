#!/bin/bash

# Setup LDAP from scratch and install all pertinent data for Testing
BASE_DIR="galahad/deploy/setup"
LDAP_SCRIPTS_DIR="ldap"

# Install openldap and virtue specific schema and data
sudo $HOME/$BASE_DIR/$LDAP_SCRIPTS_DIR/install_ldap.sh
$HOME/$BASE_DIR/$LDAP_SCRIPTS_DIR/add_canvas_schema.sh
$HOME/$BASE_DIR/$LDAP_SCRIPTS_DIR/add_ldap_backend.sh
$HOME/$BASE_DIR/$LDAP_SCRIPTS_DIR/create_base_ldap_structure.py
