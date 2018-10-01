import rethinkdb as r


def add_router_instance_to_galahad_table(instance_id, private_ip, guestnet_ip="10.91.0.254"):
    r.connect(
        host="rethinkdb.galahad.com",
        port=28015,
        ssl={
            'ca_certs': '/var/private/ssl/rethinkdb_cert.pem'
        }).repl()

    r.db('transducers').table('galahad').insert([
        {"host": instance_id,
         "function": "router",
         "address": private_ip,
         "guestnet": guestnet_ip}]).run()
