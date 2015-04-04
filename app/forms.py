from flask.ext.wtf import Form
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length

class CreateLoginForm(Form):
    username = StringField('Username', validators=[DataRequired()])
    password1 = StringField('Password', validators=[DataRequired(), Length(min=10)])
    password2 = StringField('Confirm Password', validators=[DataRequired(), Length(min=10)])
