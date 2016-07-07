import datetime

from flask_wtf import Form
from wtforms.ext.dateutil.fields import DateField
from wtforms.fields import BooleanField, DecimalField
from wtforms.validators import (
    InputRequired, NumberRange, Optional, ValidationError)

from .models import QRCode, QRUse

class ConfirmationForm(Form):
    confirmed = BooleanField(
        'Used the code?', default='checked', validators=[Optional()])
    free_amount = DecimalField(
        'Free meal value?',
        validators=[Optional(), NumberRange(min=0, max=500)])

class UsageForm(Form):
    when = DateField('Date used', validators=[InputRequired()])
    free_amount = DecimalField(
        'Free meal value?',
        validators=[Optional(), NumberRange(min=0, max=500)])

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
