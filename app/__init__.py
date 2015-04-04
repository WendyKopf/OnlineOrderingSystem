from flask import Flask
from flask.ext.bcrypt import Bcrypt

# The main web app
app = Flask(__name__)
app.config.from_object('config') # Load config.py

# Password encryption library
bcrypt = Bcrypt(app)

# Start web app
from app import views
