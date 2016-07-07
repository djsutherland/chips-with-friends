from __future__ import unicode_literals
import datetime

from flask import abort, redirect, render_template, url_for
from flask_login import current_user
from flask_security import login_required

from .app import app
from .models import User, QRCode, QRUse


@app.route('/')
@login_required
def index():
    me = User(**current_user._data)
    my_uses = QRUse.select().where(QRUse.user == me)
    return render_template('index.html', my_uses=my_uses)


@app.route('/use/')
@login_required
def pick_barcode():
    me = User(**current_user._data)
    qr = QRCode.get()  # FIXME logic here
    qr_use = QRUse(user=me, qr_code=qr, when=datetime.datetime.now(),
                   confirmed=None)
    qr_use.save()
    return redirect(url_for('use', use_id=qr_use.id))


@app.route('/use/<int:use_id>/')
@login_required
def use(use_id):
    try:
        use = QRUse.get(QRUse.id == use_id)
    except QRUse.DoesNotExist:
        return abort(404)
    return render_template('use.html', use=use)


@app.route('/use/confirm/<int:use_id>/')
@login_required
def use_confirm(use_id):
    try:
        use = QRUse.get(QRUse.id == use_id)
    except QRUse.DoesNotExist:
        return abort(404)

    use.confirmed = True
    use.save()
    return render_template('confirm.html', use=use)


@app.route('/use/cancel/<int:use_id>/')
@login_required
def use_cancel(use_id):
    try:
        use = QRUse.get(QRUse.id == use_id)
    except QRUse.DoesNotExist:
        return abort(404)

    use.confirmed = False
    use.save()
    return render_template('cancel.html', use=use)
