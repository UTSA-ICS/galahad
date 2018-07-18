ssh-keyscan -H $2 >> /root/.ssh/known_hosts
xl migrate $1 $2
python ~/galahad/gaius/gaius/bin/alert.py
ssh-keygen -R $2
rm /root/.ssh/known_hosts.old
