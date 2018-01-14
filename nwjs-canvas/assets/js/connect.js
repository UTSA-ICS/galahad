'use strict';

const Client = require('ssh2').Client;
const net = require('net');

//console.warn('UTILS:  ', Client.utils);

// 3. forward out
function forwardConnection(conn, options) {
  console.warn('forwarding client to VirtUE');
  conn.forwardOut(options.srcAddr, options.srcPort, options.dstAddr, options.dstPort, function(err, stream) {
    if (err) {
      console.error('FORWARD OUT ERROR! ', err);
      throw err;
    }
    console.warn('forwarded stream: ', stream);
    stream.on('close', function() {
      console.warn('TCP :: CLOSED');
      conn.end();
    }).on('data', function(data) {
      console.warn('TCP :: DATA: ' + data);
    });
  });
}

// 2. create client server
function createClientServer(conn, options) {
  const server = net.createServer((c) => {
    // 'connection' listener
    c.on('end', () => {
      console.warn('client disconnected');
    });
    // forward local connection to VirtUE VM
    forwardConnection(conn, options);
  });
  server.on('error', (err) => {
    console.error('CLIENT SERVER ERROR: ', err);
    throw err;
  });
  server.listen(options.localPort, options.localAddr, () => {
    console.warn('client server listening on port ', server.address().port);
  });
}
// 1. Connect to VirtUE VM
function openTunnel(options) {
  let debugFunc = (data) => {
    console.log(Date(), data);
  }
  let conn = new Client();
  conn.on('ready', function() {
    console.warn('tunnel open');
    // spin up client server
    createClientServer(conn, options)
  }).connect({
    host: options.dstAddr,
    port: 22,
    username: 'test',
    password: 'test123',
    debug: debugFunc
  });
}

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


module.exports.openTunnel = openTunnel;
