from flask_wtf import Form
from wtforms.fields import BooleanField, DecimalField
from wtforms.validators import NumberRange, Optional


class ConfirmationForm(Form):
    used = BooleanField(
        'Used the code?', default='checked', validators=[Optional()])
    amount_saved = DecimalField(
        'Amount redeemed free',
        validators=[Optional(), NumberRange(min=0, max=500)])
