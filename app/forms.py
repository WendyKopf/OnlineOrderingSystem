from flask.ext.wtf import Form
from wtforms import BooleanField, StringField, PasswordField
from wtforms.ext.sqlalchemy.orm import model_form
from wtforms.validators import DataRequired, Length

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
    
#I think we should have a secondary page once the add user page is submitted
#for specialization into the database.
#for instance, adding a user, then if the employee checkbox is selected, then the 
#add user would be rerouted to a second form with specifics for employee info
# loginform-> isemployee->yes -> employee specific page to add manager/commission/etc.
#                       ->no  -> client specific page to add salesperson/company/etc.

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

ProductForm  = model_form(models.Product, base_class=Form)
