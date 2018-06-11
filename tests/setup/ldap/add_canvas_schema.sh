#!/bin/bash

sudo ldapadd -Q -Y EXTERNAL -H ldapi:/// -f ~/galahad/tests/setup/ldap/openldap/cn\=canvas.ldif -w Test123!
