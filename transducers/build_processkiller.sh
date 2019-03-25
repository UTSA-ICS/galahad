#!/bin/bash

set -e

TRANSDUCERS_HOME=$HOME/galahad/transducers

cd $TRANSDUCERS_HOME
mkdir -p $TRANSDUCERS_HOME/processkiller/opt/processkiller
./build_deb.sh processkiller
