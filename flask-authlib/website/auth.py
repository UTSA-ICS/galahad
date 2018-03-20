from functools import wraps
from authlib.flask.client import OAuth
from authlib.client.apps import register_apps
from werkzeug.local import LocalProxy
from flask import g, session
from flask import url_for, redirect, request
from .models import User, cache


def login(user, permanent=True):
    print('WAT    : user.id = ' + repr(user.id))
    session['sid'] = user.id
    session.permanent = permanent
    g.current_user = user


def logout():
    if 'sid' in session:
        del session['sid']


def get_current_user():
    user = getattr(g, 'current_user', None)
    print('WAT    : getattr = ' + repr(user))
    if user:
        return user

    sid = session.get('sid')
    print('WAT    : sid = ' + repr(sid))
    if not sid:
        return None

    user = User.query.get(sid)
    print('WAT    : query = ' + repr(user))
    if not user:
        logout()
        return None

    g.current_user = user
    return user


current_user = LocalProxy(get_current_user)

def require_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user:
            url = url_for('account.login', next=request.path)
            return redirect(url)
        return f(*args, **kwargs)
    return decorated
