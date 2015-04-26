from flask.ext.wtf import Form
from wtforms import StringField, PasswordField
from wtforms.ext.sqlalchemy.orm import model_form
from wtforms.validators import DataRequired, Length

import models


class CreateLoginForm(Form):
    username = StringField('Username', validators=[DataRequired()])
    password1 = StringField('Password', validators=[DataRequired(), Length(min=10)])
    password2 = StringField('Confirm Password', validators=[DataRequired(), Length(min=10)])

EmployeeForm = model_form(models.Employee, Form, exclude_pk=True) 
ClientForm   = model_form(models.Client, Form, exclude_pk=True) 
ProductForm  = model_form(models.Product, base_class=Form)
