# Copyright (c) 2019 by Star Lab Corp.

from functools import wraps
from werkzeug.local import LocalProxy
from flask import g, session
from flask import url_for, redirect, request
from .models import User


def login(user, permanent=True):
    session['sid'] = user.id
    session.permanent = permanent
    g.current_user = user


def logout():
    if 'sid' in session:
        del session['sid']


def get_current_user():
    user = getattr(g, 'current_user', None)
    if user:
        return user

    sid = session.get('sid')
    if not sid:
        return None

    user = User.query.get(sid)
    if not user:
        logout()
        return None

    g.current_user = user
    return user


current_user = LocalProxy(get_current_user)


def require_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        print('WAT    : enter decorated')
        if not current_user:
            print('WAT    : not current_user')
            url = url_for('account.login', next=request.path)
            return redirect(url)
        return f(*args, **kwargs)

    return decorated
