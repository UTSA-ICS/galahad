#!/bin/bash

PORT=""
if [ "$#" -ne 1 ]; then
  echo "#########################################################################################"
  echo "ERROR: No Port number specified. Please pass in flask PORT! .e.g. 5000, 5002 etc."
  echo "#########################################################################################"
  exit
else
  PORT=$1
  echo "Port to be used is $PORT"
fi

# Get the current directory
current_dir=$(pwd)
# Now get the last field in the directory structure - This should be
# the parent directory from where this script is being called.
dir=$(echo ${current_dir##*/})

# Ensure that this script is being run from the correct directory
if [[ $dir != "excalibur" ]]; then
  echo "#########################################################################################"
  echo "ERROR: Incorrect directory detected!!"
  echo "ERROR: The current parent directory is not [excalibur]"
  echo "ERROR: Please ensure this script is being run from \$HOME/galahad/excalibur directory"
  echo "#########################################################################################"
else

  if [ ! -d "venv" ]; then
    sudo apt install -y virtualenv
    virtualenv venv
    source ./venv/bin/activate
    pip install -r ./requirements.txt
  fi

  source ./venv/bin/activate

  # These are needed to initialize flask's database
  export FLASK_APP=app.py
  export FLASK_DEBUG=1

  if [ ! -f "conf/dev.config.py" ]; then
    # Specify the SQLite DB file's location in the generated config
    # Get the directory path without the 'excalibur' dir
    directory_path=$(sed 's/\/excalibur//' <<< $current_dir)
    # Now create the config file for the database.
    mkdir -p conf
    cat <<-EOF > conf/dev.config.py
	SECRET_KEY = 'your_secret'
	SQLALCHEMY_DATABASE_URI = 'sqlite:///$directory_path/excalibur/website/sqlite.db'
	OAUTH_CACHE_DIR = '_cache'
	EOF
  fi

  if [ ! -f "website/sqlite.db" ]; then
    # Initialize the database.
    flask initdb
  fi

  # Copy SSL Certs from galahad-config repo
  if [ ! -d "ssl" ] || [ ! -f "ssl/flask_ssl.cert" ] || [ ! -f "ssl/flask_ssl.key" ]; then
    mkdir -p ssl
    # Remove the excalibur dir
    base_dir=$(sed 's/\/excalibur//' <<< $current_dir)
    # Get the directory name that the repo is checked out in
    galahad_dir=$(echo ${base_dir##*/})
    # Remove the base repo checked out dir name
    base_dir=$(sed "s/\/$galahad_dir//" <<< $base_dir)
    # This is the root dir where the config repo should be
    galahad_config_dir=$base_dir/galahad-config
    if [ ! -d "$galahad_config_dir" ]; then
      echo "#########################################################################################"
      echo "ERROR: Config directory $galahad_config_dir does not exist"
      echo "Please ensure that [$galahad_config_dir/flask_ssl] exists with the relevant SSL certs"
      echo "#########################################################################################"
      exit
    fi
    cp -R $galahad_config_dir/flask_ssl/* ssl/.
  fi

  python app.py $PORT
fi
