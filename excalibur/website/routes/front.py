# Copyright (c) 2019 by Star Lab Corp.

from flask import Blueprint
from flask import render_template
from ..auth import current_user

bp = Blueprint('front', __name__)


@bp.route('/')
def home():
    return render_template('home.html')
