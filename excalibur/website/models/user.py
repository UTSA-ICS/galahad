import datetime

from sqlalchemy import Column
from sqlalchemy import (Integer, String, DateTime)
from werkzeug.security import generate_password_hash, check_password_hash

from .base import db, Base
from ..ldaplookup import LDAP
from ..create_ldap_users import update_ldap_users_from_ad


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    _password = Column('password', String(100))
    name = Column(String(80))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )
    conn = None

    def validate_login(self, email, password):
        self.conn = LDAP(email, password)
        if not self.conn.bind_ad():
            return False

        # Update ldap users from AD user list
        update_ldap_users_from_ad()

        return True

    def query_name(self, password):
        self.conn = LDAP(self.email, password)
        if self.conn.bind_ad():
            cn = self.email.split("@")[0]
            r = self.conn.query_ad('sAMAccountName', cn)[0][1]
            self.name = r['cn'][0]
        else:
            print('ERROR: Failed to Bind to AD during call to query_name()')

    def get_user_id(self):
        return self.id

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, raw):
        self._password = generate_password_hash(raw)

    def check_password(self, raw):
        if not self._password:
            return False
        return check_password_hash(self._password, raw)

    @classmethod
    def get_or_create(cls, profile):
        user = cls.query.filter_by(email=profile.email).first()
        if user:
            return user
        user = cls(email=profile.email, name=profile.name)
        user._password = '!'
        with db.auto_commit():
            db.session.add(user)
        return user

    def to_dict(self):
        return dict(id=self.id, name=self.name)
