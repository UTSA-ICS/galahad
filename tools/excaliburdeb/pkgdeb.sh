#!/bin/bash
rm -rf deb/var/opt/excalibur/*
cp ../../excalibur/* deb/var/opt/excalibur/
dpkg-deb --build deb
