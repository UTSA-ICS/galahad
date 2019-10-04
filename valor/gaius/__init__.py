import rethinkdb as r

RT_IP = "rethinkdb.galahad.com"
RT_PORT = 28015
RT_CERT = {"ca_certs": "/mnt/efs/galahad-keys/rethinkdb_cert.pem"}
RT_CONN = r.connect(RT_IP, RT_PORT, ssl=RT_CERT)

RT_DB = "transducers"
RT_VALOR_TB = "galahad"
RT_TRANS_TB = "transducer"
RT_COMM_TB = "commands"
RT_ACK_TB = "acks"
RT_ARC_TB = "archive"

CFG_OUT = "./cfg/"
