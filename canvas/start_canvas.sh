#!/usr/bin/env bash

#
# Cleanup any leftover ssh Tunnels
#
PIDS=$(ps  auxww |grep ssh |grep "10.91." |awk {'print $2'})
for pid in $PIDS
do
    echo "Found ssh Tunnel with PID [$pid]. Cleaning it up..."
    $(kill $pid)
done

# Base directory for Canvas related files
CANVAS_DIR="galahad/canvas"

cd $HOME/$CANVAS_DIR
$HOME/nwjs-sdk-*/nw --enable-transparent-visuals --disable-gpu --disable-gpu-compositing --force-cpu-draw .

#
# Cleanup any leftover ssh Tunnels
#
PIDS=$(ps  auxww |grep ssh |grep "10.91." |awk {'print $2'})
for pid in $PIDS
do
    echo "Found ssh Tunnel with PID [$pid]. Cleaning it up..."
    $(kill $pid)
done
