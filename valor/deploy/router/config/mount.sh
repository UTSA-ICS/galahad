DIR=/mnt/nfs
if [ ! -d "$DIR" ]; then
	mkdir /mnt/nfs
fi
mount -t nfs -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport fs-de078b96.efs.us-east-1.amazonaws.com:/export /mnt/nfs
