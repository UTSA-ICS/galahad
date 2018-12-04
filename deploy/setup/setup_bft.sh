#!/bin/bash

# Install everything required for testing, except the openldap server
BASE_DIR="galahad/deploy/setup"

# Install repo for nodejs for BFT (LTS version of nodejs)
curl -sL https://deb.nodesource.com/setup_8.x | sudo bash -
sudo apt-get install -y nodejs
sudo apt-get autoremove -y

# Compile front-end
cd /home/ubuntu/galahad/blue_force_track/front_end/blue-force-track/
npm install
npm run-script build

# Set up back-end and put front-end in place
cd /home/ubuntu/galahad/blue_force_track/back_end/src/
npm install
cp -r /home/ubuntu/galahad/blue_force_track/front_end/blue-force-track/dist/ front_end/
chmod +x index.js

# Set up systemctl to run app
sudo cp /home/ubuntu/galahad/blue_force_track/bft.service /etc/systemd/system/
sudo systemctl enable bft
sudo systemctl start bft
