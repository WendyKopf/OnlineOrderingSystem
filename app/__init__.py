from flask import Flask
from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager
from flask.ext.sqlalchemy import SQLAlchemy 

# The main web app
app = Flask(__name__)
app.config.from_object('config') # Load config.py

# SQLAlchemy DB interface
db = SQLAlchemy(app)

# Password encryption library
bcrypt = Bcrypt(app)

# Login manager 
login_manager = LoginManager()
login_manager.init_app(app)

# Start web app
from app import views, models
