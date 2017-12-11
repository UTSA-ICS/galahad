import os

from flask import (Flask, request, render_template, redirect, session,
                   make_response)

from urlparse import urlparse

from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils


from __init__ import *
from client import OneLoginClient

import motor

#import dataset
#db = dataset.connect('mysql://root:test123@localhost/galahad')
#virtues = db['virtues']
#users = db['users']

#import MySQLdb
#db = MySQLdb.connect(
#    host="localhost",
#    user="root",
#    passwd="test123",
#    db="galahad"
#)

#curs = db.cursor()

#print(db)

#curs.execute(INSERT INTO virtues
#	VALUES(
#		'83452f53-9f9a-4ba4-9001-bc1329b5dfda', 'test user', 'role 1', '("app1", "app2", "app3")', '("rsrc1", "rsrc2", "rsrc3")', '("none")', "RUNNING", '127.0.0.1'
#	);
#)

#db.begin()
#try:
#	db['virtues'].insert(dict(id='83452f53-9f9a-4ba4-9001-bc1329b5dfda', username='test user', roleId='1', applicationIds='("a", "b", "c")', resourceIds='("1", "2", "3")', transducerIds='("none")', state='RUNNING', ipAddress='127.0.0.1'))
#	db.commit()
#except:
#	db.rollback()

import pymongo
from pymongo import MongoClient

mclient = MongoClient()
db = client.virtue

app = Flask(__name__)
app.config['SECRET_KEY'] = 'onelogindemopytoolkit'
#app.config['SAML_PATH'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'saml')
# Using the relative path for ease
app.config['SAML_PATH'] = './saml'


def init_saml_auth(req):
    auth = OneLogin_Saml2_Auth(req, custom_base_path=app.config['SAML_PATH'])
    return auth

def prepare_flask_request(request):
    # If server is behind proxys or balancers use the HTTP_X_FORWARDED fields
    url_data = urlparse(request.url)
    return {
        'https': 'on' if request.scheme == 'https' else 'off',
        'http_host': request.host,
        'server_port': url_data.port,
        'script_name': request.path,
        'get_data': request.args.copy(),
        'post_data': request.form.copy(),
        # Uncomment if using ADFS as IdP, https://github.com/onelogin/python-saml/pull/144
        # 'lowercase_urlencoding': True,
        'query_string': request.query_string
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    errors = []
    not_auth_warn = False
    success_slo = False
    attributes = False
    paint_logout = False

    if 'sso' in request.args:
        return redirect(auth.login())
    elif 'sso2' in request.args:
        return_to = '%sattrs/' % request.host_url
        return redirect(auth.login(return_to))
    elif 'slo' in request.args:
        name_id = None
        session_index = None
        if 'samlNameId' in session:
            name_id = session['samlNameId']
        if 'samlSessionIndex' in session:
            session_index = session['samlSessionIndex']

        return redirect(auth.logout(name_id=name_id, session_index=session_index))
    elif 'acs' in request.args:
        auth.process_response()
        errors = auth.get_errors()
        not_auth_warn = not auth.is_authenticated()
        if len(errors) == 0:
            session['samlUserdata'] = auth.get_attributes()
            session['samlNameId'] = auth.get_nameid()
            session['samlSessionIndex'] = auth.get_session_index()
            self_url = OneLogin_Saml2_Utils.get_self_url(req)
            if 'RelayState' in request.form and self_url != request.form['RelayState']:
                return redirect(auth.redirect_to(request.form['RelayState']))
    elif 'sls' in request.args:
        dscb = lambda: session.clear()
        url = auth.process_slo(delete_session_cb=dscb)
        errors = auth.get_errors()
        if len(errors) == 0:
            if url is not None:
                return redirect(url)
            else:
                success_slo = True

    if 'samlUserdata' in session:
        paint_logout = True
        if len(session['samlUserdata']) > 0:
            attributes = session['samlUserdata'].items()

    return render_template(
        'index.html',
        errors=errors,
        not_auth_warn=not_auth_warn,
        success_slo=success_slo,
        attributes=attributes,
        paint_logout=paint_logout
    )


@app.route('/attrs/')
def attrs():
    paint_logout = False
    attributes = False

    if 'samlUserdata' in session:
        paint_logout = True
        if len(session['samlUserdata']) > 0:
            attributes = session['samlUserdata'].items()

    return render_template('attrs.html', paint_logout=paint_logout,
                           attributes=attributes)


@app.route('/metadata/')
def metadata():
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    settings = auth.get_settings()
    metadata = settings.get_sp_metadata()
    errors = settings.validate_metadata(metadata)

    if len(errors) == 0:
        resp = make_response(metadata, 200)
        resp.headers['Content-Type'] = 'text/xml'
    else:
        resp = make_response(', '.join(errors), 500)
    return resp


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
