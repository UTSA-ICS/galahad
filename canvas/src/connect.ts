var exec = require('child_process').exec;
var fs = require('fs');
var debug = require('debug')('connector');
const Client = require('ssh2').Client;

var config = {
      username: "ubuntu" as string,
      //password:"derp",
      host: "ec2-54-91-72-220.compute-1.amazonaws.com" as string,
      port: 22 as number,
      dstHost: "127.0.0.1" as string,
      dstPort: 2023 as number,
      localHost: "0.0.0.0" as string, //Must be 0.0.0.0 to allow world to connect 127.0.0.1 for only local machine
      localPort: 2000 as number,
      //privateKey:fs.readFileSync('key.pem')
      privateKey: "key.pem" as string,
      //keepAlive:true,
      // debug: "console.log" as string
    };

function execTunnel(options: Object) {

  let str = `ssh -i ${config.privateKey} ${config.username}@${config.host} -p ${config.port} -4 -L ${config.localPort}:${config.dstHost}:${config.dstPort} -N -o "StrictHostKeyChecking no" `
  console.warn('execTunnel str: ', str);

  debug('trying to connect with: ', str);

  exec(str, (error: any, stdout: any, stderr: any) => {
    console.warn('stdout: ', stdout);
    console.warn('stderr: ', stderr);
    console.warn('error: ', error);
      if (error) {
        debug(`exec error: ${error}`);
        return;
      }
    debug(`stdout: ${stdout}`);
      debug(`stderr: ${stderr}`);
      });
}

// Connect to AWS Xpra
execTunnel("derp");
