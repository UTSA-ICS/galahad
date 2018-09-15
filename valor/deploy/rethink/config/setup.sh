sudo /bin/bash setup_rethink.sh
echo "bind=all" >> /etc/rethinkdb/instances.d/instance1.conf
service rethinkdb restart
#python generate_env.py
