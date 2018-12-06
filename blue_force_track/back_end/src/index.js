#!/usr/bin/env node

const express = require('express');
const app = express();

const assert = require('assert');
const fs = require('fs');

const AWS = require('aws-sdk');

const ldap = require('ldapjs');
const elasticsearch = require('elasticsearch');
const r = require('rethinkdb');

//app.use(express.static(path.join(__dirname, 'front_end')))
app.use(express.static('front_end'));

var ldapClient = null;
var esClient = null;
var rdbConn = null;

// Connect to OpenLDAP (http://ldapjs.org/client.html)
function connectLDAP(callback) {
    if (ldapClient != null) {
        return callback(ldapClient);
    } 
    ldapClient = ldap.createClient({
        url: 'ldap://excalibur.galahad.com:389'
    });
    ldapClient.bind('cn=jmitchell,ou=People,dc=canvas,dc=virtue,dc=com', 'Test123!', function(err) {
        if (err) {
            console.error("Can't connect to OpenLDAP: " + err);
            return callback(null);
        } else {
            return callback(ldapClient);
        }
    });
}

// Connect to Elasticsearch
function connectElasticSearch(callback) {
    if (esClient != null) {
        return callback(esClient);
    }

    // TODO: Connect with certs
    esClient = new elasticsearch.Client({
        hosts: ['https://aggregator.galahad.com:9200'],
        httpAuth: 'admin:admin',
        ssl:{
            ca: fs.readFileSync('/home/ubuntu/galahad-config/elasticsearch_keys/ca.pem'),
            //cert: fs.readFileSync('galahad-config/elasticsearch_keys/kirk.crtfull.pem'),
            //key: fs.readFileSync('galahad-config/elasticsearch_keys/kirk.key.pem'),
            rejectUnauthorized: true
        },
        apiVersion: '5.3'
    });

    // Check connection
    esClient.ping({
        requestTimeout: 30000,
    }, function(err) {
        if (err) {
            console.error("Can't connect to Elasticsearch: " + err);
            return callback(null);
        } else {
            return callback(esClient);
        }
    });
}

// Connect to RethinkDB
function connectRethinkDB(callback) {
    if (rdbConn != null) {
        return callback(rdbConn);
    }

    // TODO: Ask people to make permissions for 'galahad' table in rethinkdb so that we can use the
    // proper accounts to access it.  Also, get rid of default account on RethinkDB!!!
    r.connect({
        host: 'rethinkdb.galahad.com', 
        port: 28015, 
        //user: 'excalibur', 
        //password: fs.readFileSync('/home/ubuntu/galahad-config/excalibur_private_key.pem'),
        //user: 'admin', password: 'admin',
        ssl:  { ca: fs.readFileSync('/home/ubuntu/galahad-config/rethinkdb_keys/rethinkdb_cert.pem') }
    }, function(err, conn) {
        if (err) {
            console.error("Can't connect to RethinkDB: " + err);
            return callback(null);
        }
        rdbConn = conn;
        return callback(rdbConn);
    });
}

// TODO: Cloudwatch test - doesn't work yet
/*
myConfig = new AWS.Config();
myConfig.update({region: 'us-east-1'});
var credentials = new AWS.SharedIniFileCredentials({profile: 'm'});
myConfig.credentials = credentials;

app.get('/cloudwatch', (req, res) => {
    console.log('hi');
    var cloudwatch = new AWS.CloudWatch({'credentials': credentials, 'region': 'us-east-1'});
    var params = {
        MetricWidget: 'CPUUtilization',
        //Namespace: 'AWS/EC2'
    }
    cloudwatch.getMetricWidgetImage(params, function (err, data) {
        if (err) console.log(err, err.stack);
        else console.log(data);
    });
    res.send('hi');
});
*/


// ==========================================================

// Figure out the ES index (once)
// TODO: This will need to be run daily
var syslog_index = function() {
    var d = new Date();
    var year = d.getFullYear();
    var month = d.getMonth() + 1; // January is 0
    if (month < 10) {
        month = '0' + month;
    }
    var day = d.getDate();
    if (day < 10) {
        day = '0' + day;
    }
    return 'syslog-' + year + '.' + month + '.' + day;
}();

app.get('/number_messages', (req, res) => {
    connectElasticSearch(function(esClient) {
        esClient.count({ index: syslog_index }, function(error, result) {
            if (error) {
                console.error('ElasticSearch error: ' + error);
            } else {
                res.send(result);
            }
        });
    });
});

app.get('/all_messages', (req, res) => {
    connectElasticSearch(function(esClient) {
        esClient.search({
            'index': syslog_index,
            'body': {
                'sort': [{ '@timestamp': { 'order': 'desc' } }]
            }
        }, function(error, result) {
            if (error) {
                console.error('ElasticSearch error: ' + error);
            } else {
                res.send(result);
            }
        });
    });
});

app.get('/messages_per_virtue/:timerange', (req, res) => {
    var range = 'h';
    var interval = 'minute';
    if (req.params.timerange === 'hour') {
        range = 'h';
        interval = '6m';
    } else if (req.params.timerange === 'day') {
        range = 'd';
        interval = '2h';
    }
    connectElasticSearch(function(esClient) {
        esClient.search({
            index: syslog_index,
            body: {
                size: 0,
                query: {
                    range: {
                        '@timestamp': {
                            gte: "now-1" + range,
                            lt: "now",
                        }
                    }
                },
                aggs: {
                    group_by_virtue: {
                        terms: {
                            field: 'VirtueID.keyword'
                        },
                        aggs: {
                            group_by_time: {
                                date_histogram: {
                                    field: '@timestamp',
                                    interval: interval
                                }
                            }
                        }
                    }
                }
            }
        }, function(error, result) {
            if (error) {
                console.error('ElasticSearch error: ' + error);
            } else {
                res.send(result);
            }
        });
    });
});

app.get('/messages_per_virtue_per_type/:timerange', (req, res) => {
    var range = 'h';
    var interval = 'minute';
    if (req.params.timerange === 'hour') {
        range = 'h';
        interval = '6m';
    } else if (req.params.timerange === 'day') {
        range = 'd';
        interval = '2h';
    }
    connectElasticSearch(function(esClient) {
        esClient.search({
            index: syslog_index,
            body: {
                //size: 0,
                query: {
                    range: {
                        '@timestamp': {
                            gte: "now-1" + range,
                            lt: "now",
                        }
                    }
                },
                aggs: {
                    group_by_virtue: {
                        terms: {
                            field: 'VirtueID.keyword'
                        },
                        aggs: {
                            group_by_type: {
                                terms: {
                                    field: 'Event.keyword'
                                },
                                aggs: {
                                    group_by_time: {
                                        date_histogram: {
                                            field: '@timestamp',
                                            interval: interval
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }, function(error, result) {
            if (error) {
                console.error('ElasticSearch error: ' + error);
            } else {
                res.send(result);
            }
        });
    });
});

app.get('/messages_per_type/:virtueid/:timerange', (req, res) => {
    var range = 'h';
    var interval = 'minute';
    if (req.params.timerange === 'hour') {
        range = 'h';
        interval = '6m';
    } else if (req.params.timerange === 'day') {
        range = 'd';
        interval = '2h';
    }
    connectElasticSearch(function(esClient) {
        esClient.search({
            index: syslog_index,
            body: {
                size: 0,
                query: {
                    match: {
                        'VirtueID': req.params.virtueid
                    }
                },
                aggs: {
                    group_by_type: {
                        terms: {
                            field: 'Event.keyword'
                        },
                        aggs: {
                            group_by_time: {
                                date_histogram: {
                                    field: '@timestamp',
                                    interval: interval
                                }
                            }
                        }
                    }
                }
            }
        }, function(error, result) {
            if (error) {
                console.error('ElasticSearch error: ' + error);
            } else {
                res.send(result);
            }
        });
    });
});

app.get('/virtues_per_valor', (req, res) => {
    query_rethinkdb('galahad', function(results_g) {
        //res.send(results);
        valors = {};
        virtues = {};
        for (var i = 0; i < results_g.length; i++) {
            element = results_g[i]
            if (element['function'] === 'valor') {
                element['virtues'] = [];
                valors[element['id']] = element;
            } else if (element['function'] === 'virtue') {
                virtues[element['virtue_id']] = element;
            }
        }
        query_rethinkdb('commands', function(results_c) {
            for (var i = 0; i < results_c.length; i++) {
                element = results_c[i];
                if ('history' in element) {
                    valor_id = element['history'][0]['valor'];
                    if (valor_id in valors) {
                        valors[valor_id]['virtues'].push(element['virtue_id']);
                    }
                }
            }
            num_virtues_per_valor = {}
            for (valor_id in valors) {
                valor = valors[valor_id];
                num_virtues_per_valor[valor['address']] = valor['virtues'].length;
            }
            res.send(num_virtues_per_valor);
        });
    });
});

app.get('/migrations_per_virtue', (req, res) => {
    query_rethinkdb('commands', function(results_c) {
        migrations_per_virtue_id = {}
        for (var i = 0; i < results_c.length; i++) {
            if (results_c[i]['type'] === 'MIGRATION') {
                if ('history' in results_c[i]) {
                    migrations_per_virtue_id[results_c[i]['virtue_id']] = results_c[i]['history'].length;
                } else {
                    migrations_per_virtue_id[results_c[i]['virtue_id']] = 0;
                }
            }
        }
        res.send(migrations_per_virtue_id);
    });
});

app.get('/virtues_per_role', (req, res) => {
    query_ldap('virtue', function(results) {
        virtues_per_role = {}
        for (var i = 0; i < results.length; i++) {
            role = results[i]['croleId'];
            if ( !(role in virtues_per_role) ) {
                virtues_per_role[role] = 0
            }
            virtues_per_role[role] += 1
        }
        res.send(virtues_per_role);
    });
});

app.get('/valors', (req, res) => {
    valors_to_virtues( function(valors) {
        res.send(valors);
    });
});

function valors_to_virtues(callback) {
    query_rethinkdb('galahad', function(results_g) {
        valors = {};
        virtues = {};
        for (var i = 0; i < results_g.length; i++) {
            element = results_g[i]
            if (element['function'] === 'valor') {
                element['virtues'] = [];
                valors[element['id']] = element;
            } else if (element['function'] === 'virtue') {
                virtues[element['virtue_id']] = element;
            }
        }
        query_rethinkdb('commands', function(results_c) {
            for (var i = 0; i < results_c.length; i++) {
                element = results_c[i];
                if ('history' in element) {
                    valor_id = element['history'][0]['valor'];
                    if (valor_id in valors) {
                        valors[valor_id]['virtues'].push(virtues[element['virtue_id']]['guestnet']);
                    }
                }
            }
            callback(Object.values(valors));
        });
    });
}

app.get('/transducer_state', (req, res) => {
    query_rethinkdb('acks', function(results) {
        res.send(results);
    });
});


app.get('/virtues', (req, res) => {
    query_ldap('virtue', function(results) {
        res.send(results);
    });
});

app.get('/roles', (req, res) => {
    query_ldap('role', function(results) {
        res.send(results);
    });
});

app.get('/users', (req, res) => {
    query_ldap('user', function(results) {
        res.send(results);
    });
});

app.get('/transducers', (req, res) => {
    query_ldap('transducer', function(results) {
        res.send(results);
    });
});

app.get('/applications', (req, res) => {
    query_ldap('application', function(results) {
        res.send(results);
    });
});

app.get('/resources', (req, res) => {
    query_ldap('resource', function(results) {
        res.send(results);
    });
});

function query_ldap(type, send_fn) {
    var opts = {
        filter: '(objectClass=OpenLDAP' + type + ')',
        scope: 'sub'
    };

    connectLDAP(function(ldapClient) {
        ldapClient.search('dc=canvas,dc=virtue,dc=com', opts, function(err, ldapr) {
            assert.ifError(err);

            results = [];

            ldapr.on('error', function(err) {
                send_fn('Error: ' + err.message);
            });

            ldapr.on('searchEntry', function(entry) {
                results.push(entry.object);
            });

            ldapr.on('end', function(result) {
                send_fn(results);
            });
        });
    });
}

function query_rethinkdb(tableName, send_fn) {
    connectRethinkDB(function(rdbConn) {
        r.db('transducers').table(tableName).run(rdbConn, function(err, cursor) {
            if (err) {
                send_fn('Error: ' + err.message);
                return;
            }
            cursor.toArray(function(err, result) {
                if (err) {
                    send_fn('Error: ' + err.message);
                    return;
                }
                send_fn(result);
            });
        });
    });
}

app.listen(3000, () => console.log('Blue Force Tracker listening on port 3000!'));
