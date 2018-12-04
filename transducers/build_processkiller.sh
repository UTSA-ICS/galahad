#!/bin/bash

set -e

GALAHAD_CONFIG_HOME=~/galahad-config
TRANSDUCERS_HOME=~/galahad/transducers

cd $TRANSDUCERS_HOME
./build_deb.sh processkiller
