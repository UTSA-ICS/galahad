export FLASK_APP=index.py
export FLASK_DEBUG=1

sed -i "s/http:\/\/[[:alnum:]-]*\./http:\/\/$(hostname)./g" ./saml/settings.json

flask run --host=0.0.0.0 --port=8000
