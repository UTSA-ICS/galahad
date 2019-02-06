#!/usr/bin/env bash

type certutil > /dev/null 2> /dev/null
if test "$?" != "0"
then
    echo "\"certutil\" command not found!"
    echo ""
    echo "Please install the \"libnss3-tools:\" package and try again"
    echo "  On ubuntu run: <sudo apt install libnss3-tools>"
    echo "Exiting setup script..."
    exit 1
fi

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

# Create the initial pki store
cd $HOME/$CANVAS_DIR
cp -R pki_store $HOME/.pki

# Download the Excalibur certificate
echo | openssl s_client -connect excalibur.galahad.com:5002 | sed -ne '/-BEGIN CERTIFICATE-/,/-END CERTIFICATE-/p' > $HOME/excalibur-cert.pem

# Install the certificate
certutil -d sql:$HOME/.pki/nssdb -A -t "PC,," -n excalibur.galahad.com -i $HOME/excalibur-cert.pem

# Download the NWJS Package and untar it
cd $HOME
wget https://dl.nwjs.io/v0.34.5/nwjs-sdk-v0.34.5-linux-x64.tar.gz
tar -xzf nwjs-sdk-v0.34.5-linux-x64.tar.gz

cd $HOME/$CANVAS_DIR
npm install

cd $HOME/$CANVAS_DIR
python3 update_config_json.py -u $1 -p $2
