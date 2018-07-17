# Copyright (c) 2018 by Raytheon BBN Technologies Corp.

from assembler.stages.core.ssh_stage import SSHStage
import time
import subprocess, os

class TransducerStage(SSHStage):
    ''' This is a gutted galahad/transducers/syslog-ng-module-setup.sh script that
        accounts for different IP addresses '''
    NAME = 'TransducerInstallStage'
    DEPENDS = ['UserStage']

    PAYLOAD_PATH = 'payload'
    MODULE_TARBALL = 'transducer-module.tar.gz'

    INSTALL_PREREQ_SCRIPT = '''#!/bin/bash
        # install latest syslog-ng
	wget -qO - http://download.opensuse.org/repositories/home:/laszlo_budai:/syslog-ng/xUbuntu_16.04/Release.key | apt-key add -
echo deb http://download.opensuse.org/repositories/home:/laszlo_budai:/syslog-ng/xUbuntu_16.04 ./ >> /etc/apt/sources.list.d/syslog-ng-obs.list
apt update && apt install syslog-ng-core=3.14.1-3 curl git -y
        # install syslog modules and its prereqs
        add-apt-repository ppa:eugenesan/ppa
        apt install syslog-ng-mod-elastic=3.14.1-3 syslog-ng-mod-elastic=3.14.1-3 syslog-ng-mod-java=3.14.1-3 syslog-ng-mod-java-common-lib=3.14.1-3 openjdk-8-jdk -y
        echo /usr/lib/jvm/java-8-openjdk-amd64/jre/lib/amd64/server >> /etc/ld.so.conf.d/java.conf
	ldconfig

        # Install pre-build module (taken from make install step of the transducer script)
        tar xzf transducer-module.tar.gz
        cd transducer-module
        mkdir -p /usr/lib/syslog-ng/3.14
        /bin/bash ./libtool   --mode=install /usr/bin/install -c   modules/transducer-controller/libtransducer-controller.la '/usr/lib/syslog-ng/3.14'
        cd ..
        rm -rf transducer-module/
        rm transducer-module.tar.gz

        # install elasticsearch searchguard deps
        curl -L -O https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-5.6.3.tar.gz
        tar -xzvf elasticsearch-5.6.3.tar.gz
        cd elasticsearch-5.6.3/
        ./bin/elasticsearch-plugin install --batch com.floragunn:search-guard-5:5.6.3-16
        mkdir /etc/syslog-ng/jars/
        cp plugins/search-guard-5/*.jar /etc/syslog-ng/jars/
        cd ..
        rm -rf elasticsearch-5.6.3/
        rm elasticsearch-5.6.3.tar.gz
        # write config files and keystores
        mv syslog-ng.conf /etc/syslog-ng/
        mv elasticsearch.yml /etc/syslog-ng/
        mv kirk-keystore.jks /etc/syslog-ng/
        mv truststore.jks /etc/syslog-ng/
        mv sshd_config /etc/ssh/
        systemctl enable syslog-ng
        systemctl start syslog-ng

        echo 172.30.128.130 rethinkdb.galahad.com >> /etc/hosts
        rm runme.sh
        '''

    ELASTIC_YML = '''cluster:
  name: docker-cluster
network:
  host: %s
path:
  home: /etc/syslog-ng
  conf: /etc/syslog-ng
searchguard.ssl.transport.enforce_hostname_verification: false
    '''

    def __init__(self, elastic_host, elastic_node, syslog_server, ssh_host, ssh_port, work_dir='.'):
        super(TransducerStage, self).__init__(ssh_host, ssh_port, work_dir=work_dir)
        self._elastic_search_host = elastic_host
        self._elastic_search_node = elastic_node
        self._syslog_server = syslog_server

    def run(self):
        if not self._has_run:
            super(TransducerStage, self).run()


            syslog_template = 'syslog-ng-virtue-node.conf.template'
            syslog_conf_filename = 'syslog-ng.conf'
            elasticsearch_filename = 'elasticsearch.yml'
            kirk_filename = 'kirk-keystore.jks'
            truststore_filename = 'truststore.jks'
            install_script_filename = 'runme.sh'
            sshd_config_filename = 'sshd_config'


            module_path = os.path.join(self.PAYLOAD_PATH, self.MODULE_TARBALL)
            kirk_path = os.path.join(self.PAYLOAD_PATH, kirk_filename)
            trust_path = os.path.join(self.PAYLOAD_PATH, truststore_filename)
            sshd_payload_path = os.path.join(self.PAYLOAD_PATH, sshd_config_filename)
            syslog_template_path = os.path.join(self.PAYLOAD_PATH, syslog_template)
            syslog_conf_path = os.path.join(self._work_dir, syslog_conf_filename)
            elasticsearch_path = os.path.join(self._work_dir, elasticsearch_filename)
            install_path = os.path.join(self._work_dir, install_script_filename)


            with open(syslog_template_path, 'r') as syslog_ng_file:
                syslog_ng_config = syslog_ng_file.read()
                with open(syslog_conf_path, 'w') as f:
                    f.write(syslog_ng_config % (self._elastic_search_node, self._syslog_server))
                self._copy_file(syslog_conf_path, syslog_conf_filename)

            with open(elasticsearch_path, 'w') as f:
                f.write(self.ELASTIC_YML % (self._elastic_search_host))
            self._copy_file(elasticsearch_path, elasticsearch_filename)

            with open(install_path, 'w') as f:
                f.write(self.INSTALL_PREREQ_SCRIPT)
            self._copy_file(install_path, install_script_filename)

            self._copy_file(module_path, self.MODULE_TARBALL)
            self._copy_file(kirk_path, kirk_filename)
            self._copy_file(trust_path, truststore_filename)
            self._copy_file(sshd_payload_path, sshd_config_filename)

            self._exec_cmd_with_retry('chmod +x %s' % (install_script_filename))
            self._exec_cmd_with_retry('sudo ./%s' % (install_script_filename))
