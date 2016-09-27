from __future__ import division, unicode_literals
from bisect import bisect
import calendar
import datetime

from flask import abort, redirect, render_template, request, url_for
from flask_login import current_user
from flask_security import login_required
from peewee import fn, JOIN, SQL

from .app import app
from .forms import UsageForm, QRCodeForm
from .models import User, QRCode, QRUse, THRESHOLDS


@app.route('/')
def index():
    if current_user.is_authenticated:
        me = User(**current_user._data)
        my_uses = me.qruse_set.order_by(QRUse.when.desc())
        n_unconfirmed = len(me.qruse_set.where(QRUse.confirmed >> None))
    else:
        my_uses = n_unconfirmed = None
    qrs = QRCode.select().order_by(
        QRCode.worst_status.desc(), QRCode.registrant)
    # TODO: sort QRs by total uses...
    return render_template(
            'index.html', my_uses=my_uses, qrs=qrs, n_unconfirmed=n_unconfirmed)


@app.route('/about/')
def about():
    return render_template('about.html')


@app.route('/use/', methods=['POST'])
@login_required
def pick_barcode():
    me = User(**current_user._data)

    # Algorithm to pick cards:
    # - First use any potentially hot cards, then medium, then mild, then nada.
    # - Within each category, use the least-used-this-month card first.
    # - Never pick a card that's been used today.
    # This might require some intervention if we're not on track, but that's ok.

    today = datetime.date.today()
    today_begin = datetime.datetime.combine(today, datetime.time.min)
    today_end = datetime.datetime.combine(today, datetime.time.max)
    month_begin = datetime.datetime.combine(
        today.replace(day=1), datetime.time.min)
    month_end = datetime.datetime.combine(
        today.replace(day=calendar.monthrange(today.year, today.month)[1]),
        datetime.time.max)

    uses_today = (QRUse.select()
                       .where(QRUse.when >= today_begin)
                       .where(QRUse.when <= today_end)
                       .where(QRUse.confirmed | (QRUse.confirmed >> None)))
    q = (QRCode
        .select(QRCode, fn.Count(QRUse.id).alias('count'))
        .join(QRUse, JOIN.LEFT_OUTER,
              on=(QRUse.qr_code == QRCode.id)
                 & (QRUse.when >= month_begin)
                 & (QRUse.when <= month_end))
        .group_by(QRCode.id)
        .order_by(QRCode.worst_status.desc(), SQL('count').asc()))
    used_today = list(QRCode.select().join(QRUse).where(QRUse.id << uses_today))
    if used_today:  # SQL breaks on empty IN queries...
        q = q.where(QRCode.id.not_in(used_today))

    if False:  # early-month: use the least-used highest-status card
        try:
            qr = q.get()
        except QRCode.DoesNotExist:
            return render_template('no_codes.html', uses_today=uses_today)
    else:
        # late-month strategy:
        # among the highest-status cards, the one closest to getting a reward
        try:
            days_left = (month_end.date() - today).days + 1
            def thresh(qr):
                next_thresh = THRESHOLDS[bisect(THRESHOLDS, qr.count)]
                uses_left = next_thresh - qr.count
                if uses_left > days_left:
                    uses_left += 10
                return -uses_left
            qr = max(
                (qr for qr in q if qr.count < 11),
                key=lambda qr: (qr.worst_status, thresh(qr)))
        except (StopIteration, ValueError):
            # ValueError: max() arg is an empty sequence
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


@app.route('/use/confirm/<int:use_id>/<int:redeemed_free>/', methods=['POST'])
@login_required
def use_confirm(use_id, redeemed_free):
    try:
        use = QRUse.get(QRUse.id == use_id)
    except QRUse.DoesNotExist:
        return abort(404)
    use.confirmed = True
    use.redeemed_free = bool(redeemed_free)
    use.save()
    return render_template('confirm.html', use=use)


@app.route('/use/confirmed/<int:use_id>/<int:redeemed_free>/')
@login_required
def use_confirmed(use_id, redeemed_free):
    try:
        use = QRUse.get(QRUse.id == use_id)
    except QRUse.DoesNotExist:
        return abort(404)
    return render_template('confirm.html', use=use)


@app.route('/use/cancel/<int:use_id>/', methods=['POST'])
@login_required
def use_cancel(use_id):
    try:
        use = QRUse.get(QRUse.id == use_id)
    except QRUse.DoesNotExist:
        return abort(404)
    use.delete_instance()
    return render_template('cancel.html', use=use)


@app.route('/use-specific/<int:qr_id>/', methods=['GET', 'POST'])
@login_required
def use_specific(qr_id):
    me = User(**current_user._data)
    try:
        qr = QRCode.get(QRCode.id == qr_id)
    except QRCode.DoesNotExist:
        return abort(404)

    use = QRUse(qr_code=qr, user=me)

    form = UsageForm(
        request.form,
        data={'when': use.when,
              'redeemed_free': 'true' if use.redeemed_free else 'false'})
    form.qr_code = qr
    form.qr_use = use

    if form.validate_on_submit():
        use.confirmed = True
        use.redeemed_free = form.redeemed_free.data == 'true'
        use.when = form.when.data
        if isinstance(use.when, datetime.date):
            use.when = datetime.datetime.combine(use.when, datetime.time(0, 0, 1))
        use.save()
        return redirect(url_for(
            'use_confirmed', use_id=use.id, redeemed_free=use.redeemed_free))
    return render_template('use-specific.html', use=use, form=form)


@app.route('/new-card/', methods=['GET', 'POST'])
@login_required
def new_card():
    form = QRCodeForm(request.form)
    if form.validate_on_submit():
        qr_code = QRCode()
        form.populate_obj(qr_code)
        s = qr_code.barcode.find('?barcode=')
        if s != -1:
            qr_code.barcode = qr_code.barcode[s + len('?barcode='):]
        qr_code.save()
        return redirect(url_for('index'))
    return render_template('new-card.html', form=form)
