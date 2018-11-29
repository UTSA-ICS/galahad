#!/bin/bash

sudo ldapadd -Q -Y EXTERNAL -H ldapi:/// -f ~/galahad/deploy/setup/ldap/openldap/back_ldap.ldif -w Test123!
