from flask.ext.wtf import Form
from wtforms import BooleanField, SelectField, StringField, PasswordField
from wtforms.ext.sqlalchemy.orm import model_form
from wtforms.validators import DataRequired, Length, NumberRange

import models
from app import db


class CreateUserForm(Form):
    username = StringField('Username', validators=[DataRequired()])
    password1 = StringField('Password', validators=[DataRequired(), Length(min=10)])
    password2 = StringField('Confirm Password', validators=[DataRequired(), Length(min=10)])
    is_employee = BooleanField('Employee?')
    
#class AddClientForm(Form):
    #client_id      = StringField('Username', validators=[DataRequired()])
    #salesperson_id = StringField('Assigned Salesperson', validators =[DataRequired()]
    #company        = StringField('Company Name' , validators = [DataRequired()]
    #password1 = StringField('Password', validators=[DataRequired(), Length(min=10)])
    #password2 = StringField('Confirm Password', validators=[DataRequired(), Length(min=10)])

class AddEmployeeForm(Form):
    username = StringField('Username', validators =[DataRequired()])
    password1 = StringField('Password', validators=[DataRequired(), Length(min=10)])
    password2 = StringField('Confirm Password', validators=[DataRequired(), Length(min=10)])
    managedBy = StringField('Managed by', validators =[DataRequired()])
    commission = StringField('Commission' , validators = [DataRequired()])
    maxDiscount = StringField('Max Discount' , validators =[DataRequired()])
    title = StringField('Title' , validators =[DataRequired()])
    
    
class LoginForm(Form):
    username = StringField('Username', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])

ClientForm = model_form(models.Client,
                        base_class=Form, 
                        db_session=db.session,
                        exclude=['password_hash', 'is_employee', 'active'])
class AddClientForm(ClientForm):
    password1 = StringField('Password', validators=[DataRequired(), Length(min=10)])
    password2 = StringField('Confirm Password', validators=[DataRequired(), Length(min=10)])
    salesperson_id = SelectField(u'Salesperson', coerce=int)


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
