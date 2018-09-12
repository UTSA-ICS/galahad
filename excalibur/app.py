import os
import sys
import logging
from website import create_app
from website.models import db
import ssl

from elastic_log_handler.handlers import CMRESHandler


app = None
is_dev = bool(os.getenv('FLASK_DEBUG'))



if is_dev:
    os.environ['AUTHLIB_INSECURE_TRANSPORT'] = 'true'
    conf_file = os.path.abspath('conf/dev.config.py')
    app = create_app(conf_file)

    @app.after_request
    def add_header(resp):
        resp.headers['Cache-Control'] = 'no-store'
        resp.headers['Pragma'] = 'no-cache'
        return resp
else:
    app = create_app()


@app.before_first_request
def initialize_logger():
    setup_logging('elasticsearch.galahad.com', '/var/private/ssl/elasticsearch_keys/kirk.crtfull.pem',
                  '/var/private/ssl/elasticsearch_keys/kirk.key.pem', 'admin', 'admin',
                  '/var/private/ssl/elasticsearch_keys/ca.pem')


@app.cli.command()
def initdb():
    db.create_all()
    print('WAT: db created')


def main():
    # process command line arguments
    flask_port = int(sys.argv[1])

    # Use generated certs for SSL/HTTPS
    # For SSLContext its better to use TLS rather than
    # SSLv3 due to a POODLE vulnerability.
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain('ssl/flask_ssl.cert', 'ssl/flask_ssl.key')

    # Run the flask server with appropriate options
    app.run(host='0.0.0.0', port=flask_port, debug=True, ssl_context=context)


def setup_logging(es_host, es_cert, es_key, es_user, es_pass, es_ca):
    elasticLog = logging.getLogger('elasticLog')
    elasticHandler = CMRESHandler(hosts=[{'host': es_host, 'port': 9200}],
                                  auth_type=CMRESHandler.AuthType.HTTPS,
                                  es_index_name="excalibur",
                                  use_ssl=True,
                                  # This should only be false for development purposes.  Production should have certs that pass ssl verification
                                  verify_ssl=False,
                                  buffer_size=2,
                                  flush_frequency_in_sec=1000,
                                  ca_certs=es_ca,
                                  client_cert=es_cert,
                                  client_key=es_key,
                                  auth_details=(es_user, es_pass),
                                  index_name_frequency=CMRESHandler.IndexNameFrequency.DAILY,
                                  raise_on_indexing_exceptions=True)
    elasticLog.addHandler(elasticHandler)
    elasticLog.setLevel(logging.INFO)


if __name__ == "__main__":
    main()
