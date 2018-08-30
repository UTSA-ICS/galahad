cp /mnt/efs/base_config.cfg ./config/$1.cfg
sed -i "s/\$NAME/$1/g" ./config/$1.cfg
sed -i "s/\$VIRTUE/$2/g" ./config/$1.cfg
sed -i "s/\$VALOR/$3/g" ./config/$1.cfg
sed -i "s%\$PATH%$4%g" ./config/$1.cfg

xl create ./config/$1.cfg
