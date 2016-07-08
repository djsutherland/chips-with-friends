from __future__ import unicode_literals
import random
import string

from flask import render_template
from flask_security import Security, PeeweeUserDatastore
from flask_social import Social
from flask_social.datastore import PeeweeConnectionDatastore
from flask_social.utils import get_connection_values_from_oauth_response
from flask_social.views import connect_handler, login_user, login_failed

from .app import app, db
from .models import Role, User, UserRoles, Connection


user_datastore = PeeweeUserDatastore(db, User, Role, UserRoles)
app.security = Security(app, user_datastore)
app.social = Social(app, PeeweeConnectionDatastore(db, Connection))


@login_failed.connect_via(app)
def on_login_failed(sender, provider, oauth_response):
    connection_values = get_connection_values_from_oauth_response(
        provider, oauth_response)
    name = connection_values['full_name']
    if isinstance(name, dict):
        try:
            name = '{} {}'.format(name['givenName'], name['familyName'])
        except (ValueError, KeyError):
            pass
    password = ''.join(random.choice(string.ascii_letters) for _ in range(20))
    user, new = User.get_or_create(
            name=name, defaults={'email': '', 'password': password})
    # don't bother using the datastore, just use the model

    connection_values['user_id'] = user.id
    connect_handler(connection_values, provider)
    login_user(user)
    db.commit()
    return render_template('index.html')
