#!/bin/bash

sudo ldapadd -Q -Y EXTERNAL -H ldapi:/// -f /home/ubuntu/galahad/tests/virtue-ci/openldap/cn\=canvas.ldif -w Test123!
