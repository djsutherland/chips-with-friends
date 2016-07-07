from flask_wtf import Form
from wtforms.fields import BooleanField, DecimalField
from wtforms.validators import NumberRange, Optional


class ConfirmationForm(Form):
    confirmed = BooleanField(
        'Used the code?', default='checked', validators=[Optional()])
    free_amount = DecimalField(
        'Free meal value?',
        validators=[Optional(), NumberRange(min=0, max=500)])
