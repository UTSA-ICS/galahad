#!/bin/bash

# Ensure that this script is being run from the correct directory
if [ ! -f app.py ]; then
  echo ""
  echo "#########################################################################################"
  echo "ERROR: Incorrect directory detected!!"
  echo "ERROR: Unable to find file app.py in current directory"
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
    # Initialize the database.
    flask initdb
  fi

  source ./venv/bin/activate
  export FLASK_APP=app.py
  export FLASK_DEBUG=1

  python app.py 5002
fi
