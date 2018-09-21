import rethinkdb as r

RT_IP="172.30.1.54"
RT_PORT=28015
RT_CONN=r.connect(RT_IP,RT_PORT)

RT_DB="routing"
RT_VALOR_TB="galahad"
RT_TRANS_TB="transducer"
RT_COMM_TB="commands"
RT_ACK_TB="acks"
RT_ARC_TB="archive"

CFG_OUT="./cfg/"
