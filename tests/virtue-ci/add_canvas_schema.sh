#!/bin/bash

sudo ldapadd -Q -Y EXTERNAL -H ldapi:/// -f /home/ubuntu/openldap/cn\=canvas.ldif -w Test123!
