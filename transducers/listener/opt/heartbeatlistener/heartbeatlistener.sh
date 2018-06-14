HEARTBEAT_LISTENER_HOME=/opt/heartbeatlistener
cd $HEARTBEAT_LISTENER_HOME
# Check if the virtual environment directory exists
# If not then create a virtual environment called "vnev"
# Then install all the python dependencies and as this is the
if [ ! -d "venv" ]; then
  sudo apt install virtualenv
  virtualenv venv
  source ./venv/bin/activate
  pip install -r ./requirements.txt  
else
  source ./venv/bin/activate
fi
# Now start the listener
python /opt/heartbeatlistener/listener.py .excalibur
