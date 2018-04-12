from stages.core.ssh_stage import SSHStage
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
apt update && apt install syslog-ng-core curl git -y
        # install syslog modules and its prereqs
        add-apt-repository ppa:eugenesan/ppa
        apt install syslog-ng-mod-elastic openjdk-8-jdk -y
        echo LD_LIBRARY_PATH=/usr/lib/jvm/java-8-openjdk-amd64/jre/lib/amd64/server/ >> /etc/default/syslog-ng

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
        systemctl enable syslog-ng
        systemctl start syslog-ng

        echo 172.30.128.130 rethinkdb.galahad.com >> /etc/hosts
        rm runme.sh
        '''

    SYSLOG_VIRTUE_NODE_CONF = '''@version: 3.14
@module mod-java
@include "scl.conf"


source s_local { systemd-journal(); internal(); };

destination d_file { file("/var/log/syslog-ng-msg"); };

destination d_elastic {
	elasticsearch2(
		client-lib-dir("/etc/syslog-ng/jars/")
		index("syslog-${YEAR}.${MONTH}.${DAY}")
		type("syslog")
		time-zone("UTC")
		client-mode("https")
		cluster("docker-cluster")
		cluster-url("%s")
		java_keystore_filepath("/etc/syslog-ng/kirk-keystore.jks")
		java_keystore_password("changeit")
		java_truststore_filepath("/etc/syslog-ng/truststore.jks")
		java_truststore_password("changeit")
		http_auth_type("clientcert")
		resource("/etc/syslog-ng/elasticsearch.yml")
		template("$(format-json --scope rfc3164 --scope nv-pairs --exclude DATE @timestamp=${ISODATE})")
	);
};

destination d_network { syslog("%s" transport("tcp") template("${S_ISODATE} ${MESSAGE}\n")); };


parser message_parser {
	kv-parser(value-separator(":"));
};

parser transducer_controller {
	transducer_controller();
};

log { 
	source(s_local); 
	filter { match("kernel" value("PROGRAM")) or match("winesrv" value("PROGRAM")) };
    	parser(message_parser);
	parser(transducer_controller);
    	filter { not match("syslog-ng" value("ProcName")) };
	destination(d_file);
	destination(d_elastic);
	destination(d_network);
};
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

    def run(self):
        if not self._has_run:
            super().run()

            syslog_conf_filename = 'syslog-ng.conf'
            elasticsearch_filename = 'elasticsearch.yml'
            kirk_filename = 'kirk-keystore.jks'
            truststore_filename = 'truststore.jks'
            install_script_filename = 'runme.sh'


            module_path = os.path.join(self.PAYLOAD_PATH, self.MODULE_TARBALL)
            kirk_path = os.path.join(self.PAYLOAD_PATH, kirk_filename)
            trust_path = os.path.join(self.PAYLOAD_PATH, truststore_filename)
            syslog_conf_path = os.path.join(self._work_dir, syslog_conf_filename)
            elasticsearch_path = os.path.join(self._work_dir, elasticsearch_filename)
            install_path = os.path.join(self._work_dir, install_script_filename)
            
            with open(syslog_conf_path, 'w') as f:
                f.write(self.SYSLOG_VIRTUE_NODE_CONF % (self._args.elastic_search_node, self._args.syslog_server))
            self._copy_file(syslog_conf_path, syslog_conf_filename)
            
            with open(elasticsearch_path, 'w') as f:
                f.write(self.ELASTIC_YML % (self._args.elastic_search_host))
            self._copy_file(elasticsearch_path, elasticsearch_filename)

            with open(install_path, 'w') as f:
                f.write(self.INSTALL_PREREQ_SCRIPT)
            self._copy_file(install_path, install_script_filename)

            self._copy_file(module_path, self.MODULE_TARBALL)
            self._copy_file(kirk_path, kirk_filename)
            self._copy_file(trust_path, truststore_filename)

            self._exec_cmd('chmod +x %s' % (install_script_filename))
            self._exec_cmd('sudo ./%s' % (install_script_filename))
