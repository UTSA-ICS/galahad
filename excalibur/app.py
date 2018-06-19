import os
import sys
from website import create_app
from website.models import db
import ssl

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


@app.cli.command()
def initdb():
    db.create_all()
    print('WAT: db created')


def main():
    # proces command line arguments
    flask_port = int(sys.argv[1])

    # Use generated certs for SSL/HTTPS
    # For SSLContext its better to use TLS rather than
    # SSLv3 due to a POODLE vulnerability.
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain('ssl/flask_ssl.cert', 'ssl/flask_ssl.key')

    # Run the flask server with appropriate options
    app.run(host='0.0.0.0', port=flask_port, debug=True, ssl_context=context)


if __name__ == "__main__":
    main()
