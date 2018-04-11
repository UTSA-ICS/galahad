from stages.core.ssh_stage import SSHStage
import time
import subprocess, os

class MerlinStage(SSHStage):
    ''' This stage is a demo stage for how to use SSHStage tools '''
    NAME = 'MerlinStage'
    DEPENDS = ['UserStage']

    PAYLOAD_PATH = 'payload'
    DEB_FILE = 'merlin.deb'

    INIT_SCRIPT = '''#!/bin/sh
### BEGIN INIT INFO
# Provides:          merlin
# Required-Start:    $local_fs $network $named $time $syslog
# Required-Stop:     $local_fs $network $named $time $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Description:       VirtUE Merlin
### END INIT INFO

SCRIPT="python /opt/merlin/merlin.py -c /var/private/ssl/rethinkdb_cert.pem -v /var/private/ssl/virtue_1_key.pem -e /var/private/ssl/excalibur_pub.pem -r %s virtue_$(cat /etc/machine-id)"
RUNAS=merlin

PIDFILE=/opt/merlin/merlin.pid
LOGFILE=/opt/merlin/merlin.log

start() {
  if [ -f /var/run/$PIDNAME ] && kill -0 $(cat /var/run/$PIDNAME); then
    echo 'Service already running' >&2
    return 1
  fi
  echo 'Starting service...' >&2
  local CMD="$SCRIPT &> \"$LOGFILE\" & echo \$!"
  echo "Command: $CMD" >&2
  su - $RUNAS -c "$CMD" > "$PIDFILE"
  echo 'Service started' >&2
}

stop() {
  if [ ! -f "$PIDFILE" ] || ! kill -0 $(cat "$PIDFILE"); then
    echo 'Service not running' >&2
    return 1
  fi
  echo 'Stopping service...' >&2
  kill -15 $(cat "$PIDFILE") && rm -f "$PIDFILE"
  echo 'Service stopped' >&2
}

case "$1" in
  start)
    start
    ;;
  stop)
    stop
    ;;
  uninstall)
    uninstall
    ;;
  retart)
    stop
    start
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|uninstall}"
esac
''' 

    SYSTEMCTL_UNIT = '''[Unit]
After=network.target

[Service]
Type=forking
ExecStart=/etc/init.d/merlin start

[Install]
WantedBy=multi-user.target
Alias=merlin.service'''

    def run(self):
        if not self._has_run:
            super().run()
            deb_file_path = os.path.join(self.PAYLOAD_PATH, self.DEB_FILE)
            init_vmpath = '/etc/init.d/merlin'
            init_filename = os.path.basename(init_vmpath)
            init_path = os.path.join(self._work_dir, init_filename)
            systemctl_vmpath = '/etc/systemd/system/merlin.service'
            systemctl_filename = os.path.basename(systemctl_vmpath)
            systemctl_path = os.path.join(self._work_dir, systemctl_filename)

            with open(init_path, 'w') as f:
                f.write(self.INIT_SCRIPT % (self._args.rethinkdb_host))
            self._copy_file(init_path, init_filename)

            with open(systemctl_path, 'w') as f:
                f.write(self.SYSTEMCTL_UNIT)
            self._copy_file(systemctl_path, systemctl_filename)
            self._copy_file(deb_file_path, self.DEB_FILE)

            self._exec_cmd('sudo dpkg -i %s' % (self.DEB_FILE))
            self._exec_cmd('sudo chown -R merlin:virtue /opt/merlin')
            self._exec_cmd('sudo chown -R merlin:virtue /var/private/ssl')
            self._exec_cmd('sudo mv %s %s' % (init_filename, init_vmpath))
            self._exec_cmd('sudo chmod +x %s' % (init_vmpath))
            self._exec_cmd('sudo mv %s %s' % (systemctl_filename, systemctl_vmpath))
            self._exec_cmd('sudo systemctl enable merlin')
            self._exec_cmd('sudo systemctl start merlin')
            self._exec_cmd('sudo rm merlin.deb')
