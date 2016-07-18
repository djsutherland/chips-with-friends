import os

ADMINS = ['dougal@gmail.com']
DATABASE = 'sqlite:///' + os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../chip_friends.db'))

# override this in deploy.py!
SECRET_KEY = '9Zbl48DxpawebuOKcTIxsIo7rZhgw2U5qs2mcE5Hqxaa7GautgOh3rkvTabKp'

DEBUG = True
