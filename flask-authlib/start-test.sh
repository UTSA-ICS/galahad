#!/bin/bash

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
    # These are needed to initialize flask's database
    export FLASK_APP=app.py
    export FLASK_DEBUG=1
    # Update the SQLite DB file location in the config
    # Get the directory path without the 'flask-authlib' dir
    directory_path=$(sed 's/\/flask-authlib//' <<< $current_dir)
    # Now replace the placeholders with the correct directory location
    $(sed -i 's,/<USER_HOME_DIR>\/<GALAHAD_HOME_DIR>,'"$directory_path"',' $current_dir/conf/dev.config.py)
    # Initialize the database.
    flask initdb
  fi

  source ./venv/bin/activate
  export FLASK_APP=app.py
  export FLASK_DEBUG=1

  python app.py 5002
fi
