import rethinkdb as r

RT_IP="172.30.1.54"
RT_PORT=28015
RT_CONN=r.connect(RT_IP,RT_PORT)

RT_DB="routing"
RT_VALOR_TB="galahad"
RT_TRANS_TB="transducer"

CFG_OUT="./cfg/"
