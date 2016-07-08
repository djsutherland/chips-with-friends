from __future__ import unicode_literals
import datetime

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

    def __unicode__(self):
        return '{}'.format(self.name)


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

    def __unicode__(self):
        return '{} - {}'.format(self.user, self.role)


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

    def __unicode__(self):
        return '{} ({})'.format(self.user, self.provider_id)


################################################################################


class QRCode(BaseModel):
    barcode = pw.TextField()
    registrant = pw.CharField()
    phone = pw.CharField()

    def __unicode__(self):
        return "{}".format(self.registrant)

    def total_uses(self):
        return len(self.qruse_set
                       .where(QRUse.confirmed | (QRUse.confirmed >> None)))

    def uses(self):
        return self.qruse_set.where(QRUse.confirmed | (QRUse.confirmed >> None))

    def uses_on(self, date):
        begin = datetime.datetime.combine(date, datetime.time.min)
        end = datetime.datetime.combine(date, datetime.time.max)
        return self.uses().where(QRUse.when >= begin).where(QRUse.when <= end)

    def uses_today(self):
        return self.uses_on(datetime.date.today())

    def used_today(self):
        return bool(self.uses_today())


class QRUse(BaseModel):
    user = pw.ForeignKeyField(User)
    qr_code = pw.ForeignKeyField(QRCode)
    when = pw.DateTimeField()
    confirmed = pw.BooleanField(null=True, default=None)
    redeemed_free = pw.BooleanField(default=False)

    def __unicode__(self):
        s = "{} used {} on {:%m/%d}".format(self.user, self.qr_code, self.when)
        if self.redeemed_free:
            s += " (redeemed)"
        if self.confirmed is False:
            s += " (canceled)"
        elif self.confirmed is None:
            s += " (pending)"
        return s
