#!/bin/bash
#The intention is for this to be run from the local directory when someone has
# a tested version of excalibur running in a local git checkout.
#It will build a debian package to install and automatically run excalibur
#at server start time.

rm -rf deb/var/opt/excalibur/*
mkdir -p deb/var/opt/excalibur
mkdir -p pkgs
cp -r ../../excalibur/* deb/var/opt/excalibur/
dpkg-deb --build deb pkgs
