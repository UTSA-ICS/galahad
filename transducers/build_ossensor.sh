#!/bin/bash

# For building OS Sensor Transducer

set -e

TRANSDUCERS_HOME=$HOME/galahad/transducers

cd $TRANSDUCERS_HOME
mkdir -p $TRANSDUCERS_HOME/ossensor/opt/ossensor
./build_deb.sh ossensor
