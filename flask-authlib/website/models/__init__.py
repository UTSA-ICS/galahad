# flake8: noqa
from .base import Base, db, cache
from .user import User, Connect
from .oauth2 import (
    OAuth2Client, OAuth2AuthorizationCode, OAuth2Token
)

LDAP_DATABASE_URI = "ldap://ip-172-30-1-44.ec2.internal"
AD_DATABASE_URI = "ldap://EC2AMAZ-UPCI42G.virtue.com"
