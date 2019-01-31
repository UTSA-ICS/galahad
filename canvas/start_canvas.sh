#!/usr/bin/env bash

# Base directory for Canvas related files
CANVAS_DIR="galahad/canvas"

cd $HOME/$CANVAS_DIR
$HOME/nwjs-sdk-*/nw --enable-transparent-visuals --disable-gpu --disable-gpu-compositing --force-cpu-draw .
