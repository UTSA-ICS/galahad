'use strict';

var exec = require('child_process').exec;
var fs = require('fs');
var debug = require('debug')('connector');
const Client = require('ssh2').Client;

var config = {
      username:'ubuntu',
      //password:'derp',
      host:'ec2-54-91-72-220.compute-1.amazonaws.com',
      port:22,
      dstHost:'127.0.0.1',
      dstPort:2023,
      localHost:'0.0.0.0', //Must be 0.0.0.0 to allow world to connect 127.0.0.1 for only local machine
      localPort: 2000,
      //privateKey:fs.readFileSync('key.pem')
      privateKey:'key.pem',
      //keepAlive:true,
      debug:console.log
    };

function execTunnel(options) {

  debug('trying: ssh -i ' + config.privateKey + ' ' + config.username + '@' + config.host+' -p '+config.port+' -4 -L '+config.localPort+':'+config.dstHost+':'+config.dstPort+' -N');
  exec('ssh -i '+config.privateKey+' ' +config.username+'@'+config.host+' -p '+config.port+' -4 -L '+config.localPort+':'+config.dstHost+':'+config.dstPort+' -N', (error, stdout, stderr) => {
      if (error) {
        debug(`exec error: ${error}`);
        return;
      }
    debug(`stdout: ${stdout}`);
      debug(`stderr: ${stderr}`);
      });
}


// const Client = require('ssh2').Client;
// const net = require('net');
// // 3. forward out
// function forwardConnection(conn, options) {
//   console.warn('forwarding client to VirtUE');
//   conn.forwardOut(options.srcAddr, options.srcPort, options.dstAddr, options.dstPort, function(err, stream) {
//     if (err) {
//       console.error('FORWARD OUT ERROR! ', err);
//       throw err;
//     }
//     console.warn('forwarded stream: ', stream);
//     stream.on('close', function() {
//       console.warn('TCP :: CLOSED');
//       conn.end();
//     }).on('data', function(data) {
//       console.warn('TCP :: DATA: ' + data);
//     });
//   });
// }
//
// // 2. create client server
// function createClientServer(conn, options) {
//   const server = net.createServer((c) => {
//     // 'connection' listener
//     c.on('end', () => {
//       console.warn('client disconnected');
//     });
//     // forward local connection to VirtUE VM
//     forwardConnection(conn, options);
//   });
//   server.on('error', (err) => {
//     console.error('CLIENT SERVER ERROR: ', err);
//     throw err;
//   });
//   server.listen(options.localPort, options.localAddr, () => {
//     console.warn('client server listening on port ', server.address().port);
//   });
// }
// // 1. Connect to VirtUE VM
// function openTunnel(options) {
//   let debugFunc = (data) => {
//     console.log(Date(), data);
//   }
//   let conn = new Client();
//   conn.on('ready', function() {
//     console.warn('tunnel open');
//     // spin up client server
//     createClientServer(conn, options)
//   }).connect({
//     host: options.dstAddr,
//     port: 22,
//     username: 'test',
//     password: 'test123',
//     debug: debugFunc
//   });
// }

// // Start XPRA
// conn.exec('xpra start --bind-tcp=0.0.0.0:9876 --html=on --start-child=firefox', function(err, stream) {
//   if (err) throw err;
//   stream.on('close', function(code, signal) {
//     console.log('Stream :: close :: code: ' + code + ', signal: ' + signal);
//     conn.end();
//   }).on('data', function(data) {
//     console.log('STDOUT: ' + data);
//   }).stderr.on('data', function(data) {
//     console.error('STDERR: ' + data);
//   });
// });

module.exports.tryTunnel = execTunnel;
