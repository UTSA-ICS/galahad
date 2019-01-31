#!/usr/bin/env bash

if [[ $# != 2 ]];
then
  echo ""
  echo "Enter username and passwurd e.g"
  echo "  $0 jmitchell@virtue.com Test123!"
  echo ""
  echo ""
  exit 0
fi

# Base directory for Canvas related files
CANVAS_DIR="galahad/canvas"

# Download the NWJS Package and untar it
cd $HOME
wget https://dl.nwjs.io/v0.34.5/nwjs-sdk-v0.34.5-linux-x64.tar.gz
tar -xzf nwjs-sdk-v0.34.5-linux-x64.tar.gz

cd $HOME/$CANVAS_DIR
npm install

cd $HOME/$CANVAS_DIR
python3 update_config_json.py -u $1 -p $2
