from __future__ import unicode_literals
import calendar
import datetime

from flask_security import UserMixin, RoleMixin
import peewee as pw
from peewee import JOIN, SQL, fn

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

    @classmethod
    def with_uses(cls):
        return (cls.select(cls, fn.Count(QRUse.id).alias('count'))
                   .join(QRUse, JOIN.LEFT_OUTER).group_by(User.id)
                   .order_by(SQL('count').desc(), cls.name))


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

STATUSES = [('0', 'none'), ('1', 'mild'), ('2', 'medium'), ('3', 'hot')]
STATUS_NAME = {k: v for k, v in STATUSES}
STATUS_CODE = {v: k for k, v in STATUSES}

class QRCode(BaseModel):
    barcode = pw.TextField()
    registrant = pw.CharField()
    phone = pw.CharField()
    worst_status = pw.CharField(max_length=1, choices=STATUSES)

    def __unicode__(self):
        return "{} ({})".format(self.registrant, self.worst_status_name)

    @property
    def worst_status_name(self):
        return STATUS_NAME[self.worst_status]

    def total_uses(self):
        return len(self.qruse_set
                       .where(QRUse.confirmed | (QRUse.confirmed >> None)))

    def uses_this_month(self):
        today = datetime.date.today()
        begin = datetime.datetime.combine(
            today.replace(day=1), datetime.time.min)
        end = datetime.datetime.combine(
            today.replace(day=calendar.monthrange(today.year, today.month)[1]),
            datetime.time.max)
        return len(self.qruse_set
                       .where(QRUse.confirmed | (QRUse.confirmed >> None))
                       .where(QRUse.when >= begin).where(QRUse.when <= end))

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
