#!/bin/bash
killall nw
cd ~/galahad/canvas && ./nwjs/nw --enable-transparent-visuals --disable-gpu --disable-gpu-compositing --force-cpu-draw .
