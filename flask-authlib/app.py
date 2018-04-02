import os
import sys
from website import create_app
from website.models import db
from OpenSSL import SSL

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

    # TODO - Create a proper certificate.
    #context = SSL.Context(SSL.SSLv23_METHOD)
    #context.use_privatekey_file('flask_ssl.key')
    #context.use_certificate_file('flask_ssl.crt')

    # Create a adhoc certificate for now.
    context = 'adhoc'

    app.run(host='0.0.0.0', port=flask_port, debug=True, ssl_context=context)
 
if __name__ == "__main__":
    main()

