from __future__ import unicode_literals
import datetime

from flask import abort, redirect, render_template, url_for
from flask_login import current_user
from flask_security import login_required
from peewee import fn, JOIN, SQL

from .app import app
from .models import User, QRCode, QRUse


@app.route('/')
@login_required
def index():
    me = User(**current_user._data)
    my_uses = QRUse.select().where(QRUse.user == me)
    qrs = QRCode.select().order_by(QRCode.registrant)
    # TODO: sort QRs by total uses...
    return render_template('index.html', my_uses=my_uses, qrs=qrs)


@app.route('/use/')
@login_required
def pick_barcode():
    me = User(**current_user._data)

    today = datetime.date.today()
    begin = datetime.datetime.combine(today, datetime.time.min)
    end = datetime.datetime.combine(today, datetime.time.max)
    uses_today = (QRUse.select()
                       .where(QRUse.when.between(begin, end))
                       .where(QRUse.confirmed | (QRUse.confirmed >> None)))
    used_today = QRCode.select().join(QRUse).where(QRUse.id << uses_today)
    q = (QRCode
        .select(QRCode, fn.Count(QRUse.id).alias('count'))
        .where(QRCode.id.not_in(list(used_today)))
        .join(QRUse, JOIN.LEFT_OUTER)
        .order_by(SQL('count')))
    # FIXME: handle monthly status stuff

    qr = q.get()
    if qr.id is None:
        return render_template('no_codes.html', uses_today=uses_today)

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


@app.route('/new-card/')
@login_required
def new_card():
    return abort(500)  # FIXME
