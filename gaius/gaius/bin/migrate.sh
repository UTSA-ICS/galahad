ssh-keyscan -H $2 >> /root/.ssh/known_hosts
xl migrate $1 $2
ssh-keygen -R $2
rm /root/.ssh/known_hosts.old

