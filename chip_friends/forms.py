import datetime

from flask_wtf import Form
from wtforms.ext.dateutil.fields import DateField
from wtforms.fields import BooleanField, SelectField, StringField
from wtforms.validators import (
    InputRequired, NumberRange, Optional, ValidationError)

from .models import QRCode, QRUse

class ConfirmationForm(Form):
    # confirmed = BooleanField(
    #     'Used the code?', default='checked', validators=[Optional()])
    confirmed = SelectField(
        'Actually used it?',
        choices=[('true', "Used the code"), ('false', "Didn't use the code")])
    redeemed_free = SelectField(
        'Paid for it?',
        choices=[('false', 'Paid for the meal'),
                 ('true', 'Redeemed a free meal')])
    # redeemed_free = BooleanField(
    #     'Free meal?', default=False, validators=[Optional()])

class UsageForm(Form):
    when = DateField('Date used', validators=[InputRequired()])
    redeemed_free = SelectField(
        'Paid for it?',
        choices=[('false', 'Paid for the meal'),
                 ('true', 'Redeemed a free meal')])

    def validate_when(form, field):
        if field.data < datetime.date(2016, 7, 1):
            raise ValidationError("Chiptopia only started in July!")
        if field.data > datetime.date.today():
            raise ValidationError("You're *sure* you used this in the future?")
        # HACK: setting qr_code, qr_use is *required*
        # what's the right way to do this?
        matches = list(form.qr_code.uses_on(field.data))
        if matches and matches != [form.qr_use]:
            s = "This code was already used on {}..."
            raise ValidationError(s.format(field.data))


class QRCodeForm(Form):
    registrant = StringField('Name', validators=[InputRequired()])  # TODO: unique
    phone = StringField('Phone Number', validators=[InputRequired()])
    barcode = StringField('Barcode', validators=[InputRequired()])

    def validate_barcode(form, field):
        if not field.data.startswith('https://chipotle.com/chiptopia-barcode?barcode='):
            print('{!r}'.format(field.data))
            raise ValidationError("Invalid Chiptopia barcode URL")

