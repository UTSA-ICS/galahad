#!/bin/bash

apt-get update

export DEBIAN_FRONTEND=noninteractive

echo 'slapd slapd/password1 password Test123!' | debconf-set-selections
echo 'slapd slapd/password2 password Test123!' | debconf-set-selections
echo 'slapd slapd/domain string canvas.virtue.com' | debconf-set-selections
echo 'slapd shared/organization string canvas.virtue.com' | debconf-set-selections

apt-get install slapd ldap-utils -y
