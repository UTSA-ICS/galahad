#!/bin/bash

set -e

TRANSDUCERS_HOME=$HOME/galahad/transducers

cd $TRANSDUCERS_HOME
./build_deb.sh processkiller
