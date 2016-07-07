from __future__ import unicode_literals

from flask_security import UserMixin, RoleMixin
import peewee as pw

from .app import db


class BaseModel(pw.Model):
    class Meta:
        database = db

################################################################################


class Role(BaseModel, RoleMixin):
    name = pw.CharField(unique=True)
    description = pw.TextField(null=True)


class User(BaseModel, UserMixin):
    email = pw.TextField()
    password = pw.TextField()
    active = pw.BooleanField(default=True)
    confirmed_at = pw.DateTimeField(null=True)
    name = pw.TextField()

    def __unicode__(self):
        return '{}'.format(self.name)


class UserRoles(BaseModel):
    # Because peewee does not come with built-in many-to-many
    # relationships, we need this intermediary class to link
    # user to roles.
    user = pw.ForeignKeyField(User, related_name='roles')
    role = pw.ForeignKeyField(Role, related_name='users')
    name = property(lambda self: self.role.name)
    description = property(lambda self: self.role.description)


class Connection(BaseModel):
    user = pw.ForeignKeyField(User)
    provider_id = pw.CharField()
    provider_user_id = pw.CharField(null=True)
    access_token = pw.CharField(null=True)
    secret = pw.CharField(null=True)
    display_name = pw.CharField(null=True)
    full_name = pw.CharField(null=True)
    profile_url = pw.CharField(max_length=512, null=True)
    image_url = pw.CharField(max_length=512, null=True)
    rank = pw.IntegerField(null=True)


################################################################################


class QRCode(BaseModel):
    barcode = pw.TextField()
    user = pw.ForeignKeyField(User)

    def __unicode__(self):
        return "{}".format(self.user)


class QRUse(BaseModel):
    user = pw.ForeignKeyField(User)
    qr_code = pw.ForeignKeyField(QRCode)
    when = pw.DateTimeField()
    confirmed = pw.BooleanField(null=True, default=None)

    def __unicode__(self):
        return "{} used {} on {:%m/%d}".format(self.user, self.qr_code, self.when)
