#!/bin/bash
rm -rf deb/var/opt/excalibur/*
mkdir -p deb/var/opt/excalibur
mkdir -p pkgs
cp -r ../../excalibur/* deb/var/opt/excalibur/
dpkg-deb --build deb pkgs
