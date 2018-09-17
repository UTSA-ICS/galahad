cp /mnt/nfs/vms/centos7.cfg ./config/$1.cfg
cp /mnt/nfs/vms/images/centos7.img /mnt/nfs/vms/images/$1.img
sed -i "s/\$NAME/$1/g" ./config/$1.cfg
sed -i "s/\$VIRTUE/$2/g" ./config/$1.cfg
sed -i "s/\$VALOR/$3/g" ./config/$1.cfg

xl create ./config/$1.cfg
