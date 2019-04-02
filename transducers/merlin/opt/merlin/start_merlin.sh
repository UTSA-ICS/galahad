#!/bin/sh

SCRIPT="/usr/bin/python /opt/merlin/merlin.py
         -l /opt/merlin/merlin.log
         -c /var/private/ssl/rethinkdb_cert.pem
         -v /var/private/ssl/virtue_1_key.pem
         -e /var/private/ssl/excalibur_pub.pem
         -r rethinkdb.galahad.com
         -es aggregator.galahad.com
         -ec /var/private/ssl/kirk.crtfull.pem
         -ek kirk.key.pem
         -eu admin
         -ep admin
         -ea /var/private/ssl/ca.pem
         $(cat /etc/virtue-id)"

LOGFILE=/opt/merlin/merlin-initd.log

${SCRIPT} > ${LOGFILE} 2>&1
