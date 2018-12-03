#!/bin/bash

$HOME/galahad/deploy/setup/ldap/openldap/prep_schema.py
sudo ldapadd -Q -Y EXTERNAL -H ldapi:/// -f $HOME/galahad/deploy/setup/ldap/openldap/cn\=canvas.ldif -w Test123!
