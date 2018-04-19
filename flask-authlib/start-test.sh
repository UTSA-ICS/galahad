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
if [[ $dir != "flask-authlib" ]]; then
  echo "#########################################################################################"
  echo "ERROR: Incorrect directory detected!!"
  echo "ERROR: The current parent directory is not [flask-authlib]"
  echo "ERROR: Please ensure this script is being run from \$HOME/galahad/flask-authlib directory"
  echo "#########################################################################################"
else
  # Check if the virtual environment directory exists
  # If not then create a virtual environment called "vnev"
  # Then install all the python dependencies and as this is the
  # first time flask is being run initialize the SQLALCHEMY database.
  if [ ! -d "venv" ]; then
    virtualenv venv
    source ./venv/bin/activate
    pip install -r ./requirements.txt
  fi
  # Source the virtual environment
  source ./venv/bin/activate
  # These are needed to initialize flask's database
  export FLASK_APP=app.py
  export FLASK_DEBUG=1

  # If database config file is not found then create it.
  if [ ! -f "conf/dev.config.py" ]; then
    # Specify the SQLite DB file's location in the generated config
    # Get the directory path without the 'flask-authlib' dir
    directory_path=$(sed 's/\/flask-authlib//' <<< $current_dir)
    # Now create the config file for the database.
    mkdir -p conf
    cat <<-EOF > conf/dev.config.py
	SECRET_KEY = 'your_secret'
	SQLALCHEMY_DATABASE_URI = 'sqlite:///$directory_path/flask-authlib/website/sqlite.db'
	OAUTH_CACHE_DIR = '_cache'
	EOF
  fi

  # If database does not exist then intialize it
  if [ ! -f "website/sqlite.db" ]; then
    # Initialize the database.
    flask initdb
  fi

  # Copy SSL Certs from galahad-config repo
  if [ ! -d "ssl" ] || [ ! -f "ssl/flask_ssl.cert" ] || [ ! -f "ssl/flask_ssl.key" ]; then
    mkdir -p ssl
    galahad_dir=$(sed 's/\/galahad\/flask-authlib//' <<< $current_dir)
    galahad_config_dir=$galahad_dir/galahad-config
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
