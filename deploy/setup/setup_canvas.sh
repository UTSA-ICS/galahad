#!/bin/bash

# Base directory for Canvas related files
CANVAS_DIR="galahad/canvas"

# Galahad key dir
GALAHAD_KEY_DIR="/mnt/efs/galahad-keys"

#
# Copy over the private key to use to login to the virtue
#
cp $GALAHAD_KEY_DIR/default-virtue-key.pem $CANVAS_DIR/key.pem

cd $CANVAS_DIR
echo "$HOME/nwjs-sdk-*/nw --enable-transparent-visuals --disable-gpu --disable-gpu-compositing --force-cpu-draw ." > start_canvas.sh
chmod +x start_canvas.sh


