# Copyright (c) 2019 by Star Lab Corp.

from flask import Blueprint
from flask import jsonify
from authlib.flask.oauth2 import current_token
from ..models import User
from ..services.oauth2 import require_oauth

bp = Blueprint('api_2', __name__)


@bp.route('/me')
@require_oauth()
def user_profile():
    user = User.query.get(current_token.user_id)
    return jsonify(user.to_dict())


@bp.route('/me/email')
@require_oauth('email')
def user_email():
    user = User.query.get(current_token.user_id)
    return jsonify(email=user.email)
