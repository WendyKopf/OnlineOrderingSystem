import os

# Set the absolute path of the app's base directory
basedir = os.path.abspath(os.path.dirname(__file__))

# Specify SQLite parameters for SQLAlchemy
SQLALCHEMY_DATABASE_URI = 'sqlite:///%s' % (os.path.join(basedir, 'app.db'))

# Set the locate of SQLAlchemy migration files
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

WTF_CSRF_ENABLED = True
SECRET_KEY = 'not enough entropy'
