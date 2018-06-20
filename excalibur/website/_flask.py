# coding: utf-8

import datetime
import os

from flask import Flask as _Flask
from flask.json import JSONEncoder as _JSONEncoder


class JSONEncoder(_JSONEncoder):
    def default(self, obj):

        if hasattr(obj, 'to_dict'):
            return obj.to_dict()

        if hasattr(obj, '_asdict'):
            return obj._asdict()

        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%dT%H:%M:%SZ')

        if isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')

        return _JSONEncoder.default(self, obj)


class Flask(_Flask):

    json_encoder = JSONEncoder

    jinja_options = dict(
        trim_blocks=True,
        lstrip_blocks=True,
        extensions=[
            'jinja2.ext.autoescape',
            'jinja2.ext.with_',
        ])


def create_flask_app(config=None):

    app = Flask(__name__)

    # load default configuration
    app.config.from_object('website.settings')

    # load environment configuration
    if 'WEBSITE_CONF' in os.environ:
        app.config.from_envvar('WEBSITE_CONF')

    # load app specified configuration
    if config is not None:

        if isinstance(config, dict):
            app.config.update(config)

        elif config.endswith('.py'):
            app.config.from_pyfile(config)

    return app
