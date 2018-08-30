# Python Elasticsearch Log Handler

This library provides an Elasticsearch logging appender compatible with the
python standard `logging <https://docs.python.org/2/library/logging.html>`_ library.

The code source is modified from a repo in github at `https://github.com/cmanaha/python-elasticsearch-logger
<https://github.com/cmanaha/python-elasticsearch-logger>`_

It has been modified to provide support for HTTPS connections to elasticsearch

## Requirements Python 2 

This library requires the following dependencies
 - elasticsearch
 - requests
 - enum

 ## Usage

 	from elastic_log_handler.handlers import CMRESHandler
 	elasticHandler = CMRESHandler(hosts=[{'host': es_host, 'port': 9200}],
                               auth_type=CMRESHandler.AuthType.HTTPS,
                               es_index_name="merlin",
                               use_ssl=True,
                               verify_ssl=True,
                               buffer_size=2,
                               flush_frequency_in_sec=1000,
                               ca_certs=es_ca,
                               client_cert=es_cert,
                               client_key=es_key,
							   auth_details=(es_user, es_pass),
							   index_name_frequency=CMRESHandler.IndexNameFrequency.DAILY,
							   es_additional_fields={'App': 'MyAppName', 'Environment': 'Dev'},
                               raise_on_indexing_exceptions=True)
	
	log = logging.getLogger('$LOG_NAME')
	log.setLevel(logging.INFO)
	log.addHandler(elasticHandler)


Where

* host - the URL of the elastic instance
* port - the port of the elastic instance (typically 9200)
* auth_type - The type of authorization the handler uses.  We are only using HTTPS in our deployments.
* es_index_name - The string prefix you want for the ES index's for the logs. 
* use_ssl - Use SSL to communicate with ES.  This will always be true. 
* verify_ssl - Use CA's to validate the cert of the ES server.  This will typically be true, turning off will help in debugging if the ES cert is somehow invalid.  
* buffer_size - How many log messages to save before flushing to ES.  Set this higher if a large number of log messages are generated to reduce network activity.  
* flush_frequency_in_sec - Frequency that the log buffer is flushed to ES, in seconds.  This will occur regardless of if the buffer is full or not.
* ca_certs is the path to CA cert(s) that have signed the ES server you are connecting to 
* client_cert - The client cert for this logging instance.  It should be one signed by a CA known to ES.  
* client_key - The key corresponding to the client cert.  
* auth_details - (user, pass) login information for the ES instance.  This will typically be used in our deployments.  
* index_name_frequency - How often to create a new index for this handler
es_additional_fields - Additional fields to include in the ES document sent to elasticsearch

### Importing in Galahad

To use the logging handler present in galahad, assuming your script is in galahad/dir/yourscript.py, import as follows

	sys.path.insert(0, os.path.abspath('..'))
	from elastic_log_handler.handlers import CMRESHandler

