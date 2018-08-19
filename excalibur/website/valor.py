class ValorManager:

    valors = {}
    rethinkdb_ip_address = ''


    def valor_create(self):

        valor = self.create_valor_instance()
        valor.mount_efs()
        rethinkdb.add_valor()
        router.add_valor()
        valor.setup()


    def valor_create_pool(self):
        pass


    def valor_destroy(self):
        pass


    def valor_list(self):
        pass


    def get_empty_valor(self)
        pass
