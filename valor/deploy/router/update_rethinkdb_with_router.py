#!/usr/bin/env python

# Copyright (c) 2019 by Star Lab Corp.

import rethinkdb as r
from boto.utils import get_instance_metadata


def get_instance_info():
    meta_data = get_instance_metadata(timeout=0.5, num_retries=2)

    instance_id = meta_data['instance-id']
    private_ip = meta_data['local-ipv4']

    return instance_id, private_ip


def add_router_instance_to_galahad_table(instance_id, private_ip,
                                         guestnet_ip="10.91.0.254"):
    r.connect(
        host="rethinkdb.galahad.com",
        port=28015,
        ssl={
            'ca_certs': '/mnt/efs/galahad-keys/rethinkdb_cert.pem'
        }).repl()

    r.db('transducers').table('galahad').insert([
        {
            "host": instance_id,
            "function": "router",
            "address": private_ip,
            "guestnet": guestnet_ip
        }]).run()


if __name__ == '__main__':

    instance_id, private_ip = get_instance_info()

    add_router_instance_to_galahad_table(instance_id, private_ip)
