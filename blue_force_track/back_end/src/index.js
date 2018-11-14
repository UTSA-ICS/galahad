const express = require('express');
const app = express();

const assert = require('assert');
const fs = require('fs');

const AWS = require('aws-sdk');

// Connect to OpenLDAP (http://ldapjs.org/client.html)
var ldap = require('ldapjs');
var ldapClient = ldap.createClient({
    url: 'ldap://excalibur.galahad.com:389'
});
ldapClient.bind('cn=jmitchell,ou=People,dc=canvas,dc=virtue,dc=com', 'Test123!', function(err) {
    assert.ifError(err);
});


// Connect to Elasticsearch
var elasticsearch = require('elasticsearch');

// TODO: figure out why using the cert doesn't work
var esClient = new elasticsearch.Client({
    hosts: ['https://elasticsearch.galahad.com:9200'],
    httpAuth: 'admin:admin',
    ssl:{
        ca: fs.readFileSync('/galahad-config/elasticsearch_keys/ca.pem'),
        //cert: fs.readFileSync('/galahad-config/elasticsearch_keys/kirk.crtfull.pem'),
        //key: fs.readFileSync('/galahad-config/elasticsearch_keys/kirk.key.pem'),
        rejectUnauthorized: true
    },
    apiVersion: '5.3'
});


// Connect to RethinkDB
// TODO: Ask people to make permissions for 'galahad' table in rethinkdb so that we can use the
// proper accounts to access it.  Also, get rid of default account on RethinkDB!!!
var r = require('rethinkdb');
var rdbConn = null;
r.connect({
    host: 'rethinkdb.galahad.com', 
    port: 28015, 
    //user: 'excalibur', 
    //password: fs.readFileSync('/galahad-config/excalibur_private_key.pem'),
    //user: 'admin', password: 'admin',
    ssl:  { ca: fs.readFileSync('/galahad-config/rethinkdb_keys/rethinkdb_cert.pem') }
}, function(err, conn) {
    if (err) throw err;
    rdbConn = conn;
});

app.get('/', (req, res) => res.send('Hello World!'));

// Check elasticsearch connection
app.get('/elasticsearch', (req, res) => {
 esClient.ping({
     requestTimeout: 30000,
 }, function(error) {
     if (error) {
         console.error('Can\'t connect to Elasticsearch! ' + error);
     } else {
         console.log('Everything is ok');
     }
 });
    res.send('es')
});

// TODO: testing cloudwatch, doesn't work yet
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
var syslog_index = function() {
    var d = new Date();
    var year = d.getFullYear();
    var month = d.getMonth() + 1; // January is 0
    if (month < 10) {
        month = '0' + month;
    }
    var day = d.getDay();
    if (day < 10) {
        day = '0' + day;
    }
    return 'syslog-' + year + '.' + month + '.' + day;
}();

app.get('/number_messages', (req, res) => {
    esClient.count({ index: syslog_index }, function(error, result) {
        if (error) {
            console.error('elasticsearch cluster is down! ' + error);
        } else {
            res.send(result);
        }
    });
});

app.get('/all_messages', (req, res) => {
    esClient.search({
        'index': syslog_index,
        'body': {
            'sort': [{ '@timestamp': { 'order': 'desc' } }]
        }
    }, function(error, result) {
        if (error) {
            console.error('elasticsearch cluster is down! ' + error);
        } else {
            res.send(result);
        }
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
            console.error('elasticsearch cluster is down! ' + error);
        } else {
            res.send(result);
        }
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
            console.error('elasticsearch cluster is down! ' + error);
        } else {
            res.send(result);
        }
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
            console.error('elasticsearch cluster is down! ' + error);
        } else {
            res.send(result);
        }
    });
});

app.get('/virtues_per_valor', (req, res) => {
    query_rethinkdb('galahad', function(results_g) {
        //res.send(results);
        valors = [];
        virtues = {};
        for (var i = 0; i < results_g.length; i++) {
            if (results_g[i]['function'] === 'valor') {
                results_g[i]['virtues'] = [];
                valors.push(results_g[i]);
            } else if (results_g[i]['function'] === 'virtue') {
                virtues[results_g[i]['id']] = results_g[i];
            }
        }
        query_rethinkdb('commands', function(results_c) {
            for (var i = 0; i < results_c.length; i++) {
                if ('history' in results_c[i]) {
                    valor_id = results_c[i]['history'][0]['valor'];
                    for (var j = 0; j <  valors.length; j++) {
                        if (valors[j]['id'] === valor_id) {
                            valors[j]['virtues'].push(virtues[results_c[i]['virtue_id']]['host']);
                        }
                    }
                }
            }
            num_virtues_per_valor = {}
            for (var i = 0; i < valors.length; i++) {
                valor_id = valors[i]['address'];
                num_virtues_per_valor[valor_id] = valors[i]['virtues'].length;
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
        query_rethinkdb('galahad', function(results_g) {
            num_migrations_per_virtue = {}
            for (var i = 0; i < results_g.length; i++) {
                if (results_g[i]['function'] === 'virtue' && results_g[i]['id'] in migrations_per_virtue_id) {
                    num_migrations_per_virtue[results_g[i]['host']] = migrations_per_virtue_id[results_g[i]['id']]
                }
            }
            res.send(num_migrations_per_virtue);
        });
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
        valors = [];
        virtues = {};
        for (var i = 0; i < results_g.length; i++) {
            if (results_g[i]['function'] === 'valor') {
                results_g[i]['virtues'] = [];
                valors.push(results_g[i]);
            } else if (results_g[i]['function'] === 'virtue') {
                virtues[results_g[i]['id']] = results_g[i];
            }
        }
        query_rethinkdb('commands', function(results_c) {
            for (var i = 0; i < results_c.length; i++) {
                if ('history' in results_c[i]) {
                    valor_id = results_c[i]['history'][0]['valor'];
                    for (var j = 0; j <  valors.length; j++) {
                        if (valors[j]['id'] === valor_id) {
                            valors[j]['virtues'].push(virtues[results_c[i]['virtue_id']]['host']);
                        }
                    }
                }
            }
            callback(valors);
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
}

function query_rethinkdb(tableName, send_fn) {
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
}

app.listen(3000, () => console.log('Example app listening on port 3000!'));
