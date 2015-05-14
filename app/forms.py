from flask.ext.wtf import Form
from wtforms import BooleanField, StringField, PasswordField
from wtforms.ext.sqlalchemy.orm import model_form
from wtforms.validators import DataRequired, Length, NumberRange

import models
from app import db


class CreateUserForm(Form):
    username = StringField('Username', validators=[DataRequired()])
    password1 = StringField('Password', validators=[DataRequired(), Length(min=10)])
    password2 = StringField('Confirm Password', validators=[DataRequired(), Length(min=10)])
    is_employee = BooleanField('Employee?')

class LoginForm(Form):
    username = StringField('Username', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])

ClientForm = model_form(models.Client,
                        base_class=Form, 
                        db_session=db.session,
                        exclude=['password_hash']) 
EmployeeForm = model_form(models.Employee,
                          base_class=Form,
                          db_session=db.session,
                          exclude=['password_hash']) 

ProductForm  = model_form(models.Product,
                          base_class=Form,
                          exclude=['active'],
                          field_args = {
                              'price' : { 'validators': [NumberRange(min=0.01)]},
                              'quantity' : { 'validators': [NumberRange(min=1)]}
                          })
ReorderProductForm  = model_form(models.Product, base_class=Form, exclude=['active'])
