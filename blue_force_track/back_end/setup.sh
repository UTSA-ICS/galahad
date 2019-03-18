git clone git@github.com:starlab-io/galahad-config.git
docker build -t bft .
#docker run -ti -p 3000:3000 --add-host="excalibur.galahad.com:172.30.1.44" --add-host="rethinkdb.galahad.com:172.30.1.45" --add-host="elasticsearch.galahad.com:172.30.1.46" bft
docker run -ti -p 3000:3000 bft
