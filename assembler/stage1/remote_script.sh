docker ps
while [ \$? -eq 127 ]; do
	echo "Waiting for docker"
	sleep 1
	docker ps
done
echo "{\"insecure-registries\": [ \"ajordan-desktop.bbn.com:5000\" ]}" > /etc/docker/daemon.json
service docker restart
docker pull ajordan-desktop.bbn.com:5000/virtue:virtue-gedit
git clone https://github.com/starlab-io/docker-virtue.git
cd docker-virtue/virtue
echo 'gedit|6767|' > my_virtue.config
SSHPUBKEY=$(cat /home/virtue/.ssh/authorized_keys) virtue start my_virtue.config
