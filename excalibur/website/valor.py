class ValorAPI:


    def valor_create(self):

        ValorManaager.create_valor()
       
    def valor_create_pool(self):
        pass


    def valor_destroy(self):
        pass


    def valor_list(self):
        pass



class Valor: 

    valor = {
        'amiId' : 'ami-01c5d8354c604b662',
    }


    def __init__():
        pass


    def mount_efs(self):
        '''
        mount -t nfs fs-de078b96.efs.us-east-1.amazonaws.com:/export /mnt/nfs/
        '''
        pass


    def setup(sef):a
        '''
        sudo su
        cp -r /mnt/nfs/deploy-local/compute/config /home/ubuntu/
        cd /home/ubuntu/config && /bin/bash setup.sh
        reboot (redo mounting)
        ovs-vsctl show - see bridge to remote router
        xl list - received:
             `Domain-0                       0  2048     2     r-----     198.6`
        ping 10.91.0.254 - should work
        '''
        pass



class ValorManager:

    valors = {}
    rethinkdb_ip_address = ''


    def get_empty_valor(self)
        pass


    def create_valor(self):

        valor = Valor()
        valor.mount_efs()

        RethinkDbManager.add_valor(valor)

        RouterManager.add_valor()

        valor.setup()


    def create_valor_pool(self, number_of_valors):
        pass



class RethinkDbManager:

    ip_address = ''


    def add_valor(self, valor):
        '''
        python
        import rethinkdb as r
        r.connect('localhost',28015).repl()
        print r.db('routing').table('galahad').run()
        r.db('routing').table('galahad').insert([{ new valor }]).run()
        new valor = {
           'function' : 'valor',
           'guestnet' : '10.91.0.1',
            'host'    : aws_hostname,
            'address' : aws_private_ip
        }
        '''
        pass



class RouterManager:

    ip_address = ''

    def add_valor(self, valor):
        pass
