from flask import flash, redirect, render_template

from app import app

from .forms import CreateLoginForm

from helpers import add_error

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html',
                           title='Home')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = CreateLoginForm()
    title = 'Sign Up'
    valid = form.validate_on_submit()
    if valid and form.password1.data == form.password2.data:
        flash('Data Validated!')
        flash('If we had a database setup, your login would be stored')
        return redirect('/signup')
    elif valid:
        add_error(form, 'password2', u'Passwords do not match')
        return render_template('signup.html', title=title, form=form)
    else:
        return render_template('signup.html', title=title, form=form)

@app.route('/clients/add/', methods['GET', 'POST'])
def add_client():
    form = NewCustomerForm()
    title = 'Add Clients'

    # Send user back to previous page if form errors exist
    if not form.validate_on_submit():
        return render_template('add_client.html', title=title, form=form)

    # Validate form data
    if form.password1.data != form.password2.data:
        form.errors['password2'] = u'Passwords do not match'

    if len(form.errors) == 0:
        flash('Client added')
        return redirect('/clients/')
    else:
        return render_template('add_client.html', title=title, form=form)

@app.route('/clients/', methods['GET', 'POST'])
def clients():
    title = 'All Clients'
    return render_template('clients.html', title=title)
