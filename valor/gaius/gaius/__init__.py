import rethinkdb as r

RT_HOSTNAME = "rethinkdb.galahad.com"
RT_PORT = 28015
RETHINKDB_CERT = '/var/private/ssl/rethinkdb_cert.pem'

RT_CONN=r.connect(
    host=RT_HOSTNAME,
    port=RT_PORT,
    ssl = {
        'ca_cert' : RETHINKDB_CERT
    })

RT_DB="transducers"
RT_VALOR_TB="galahad"
RT_TRANS_TB="transducer"
RT_COMM_TB="commands"
RT_ACK_TB="acks"
RT_ARC_TB="archive"

CFG_OUT="./cfg/"
