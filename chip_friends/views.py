from __future__ import unicode_literals

from flask import render_template
from flask_security import login_required

from .app import app


@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/profile')
@login_required
def profile():
    return render_template(
        'profile.html',
        content='Prifle Page',
        facebook_conn=social.facebook.get_connection())
