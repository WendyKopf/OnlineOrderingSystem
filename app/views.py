import datetime
from functools import wraps

from flask import abort, flash, g, redirect, render_template, request, session, url_for
from flask.ext.login import current_user, login_required, login_user, logout_user

from app import app, bcrypt, db, login_manager

from .forms import (
    AddClientForm, AddEmployeeForm, ClientForm, CreateUserForm, EmployeeForm, LoginForm, ProductForm,
    ReorderProductForm
)
from .models import Client, Employee, Product, Order, OrderItem, User

from helpers import add_error, flash_errors, flatten_hierarchy


###############################################################################
# Login management 
###############################################################################
login_manager.login_view = 'login'
@login_manager.user_loader
def load_user(username):
    return db.session.query(User).filter_by(username=username).first()

@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # We check the hash even if the user does not exist so that
        # we do not leak hints about the validity of a username
        user = db.session.query(User).filter_by(username=form.username.data).first()
        saved_hash = ''
        if user is not None:
            saved_hash = user.password_hash
        if bcrypt.check_password_hash(saved_hash, form.password.data):
            current_user._authenticated = True
            login_user(user, remember=True)
            return redirect(request.args.get('next') or url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html', form=form)

@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

def employees_only(titles=None):
    """A decorator to limit page access to employees."""
    def employee_wrapper(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_employee:
                abort(401)
            if titles is not None:
                emp = Employee.query.filter_by(user_id=current_user.id).first()
                if emp is None:
                    abort(503)
                if emp.title not in titles:
                    abort(401)
            return view_func(*args, **kwargs)
        return wrapped
    return employee_wrapper

###############################################################################
# Dashboard 
###############################################################################
@app.route('/')
@login_required
def dashboard():
    if current_user.is_employee:
        return employee_dashboard()
    return client_dashboard()

def employee_dashboard():
    emp = Employee.query.filter_by(user_id=current_user.id).first()
    if emp is None:
        abort(404)
    if emp.title == 'Salesperson':
        popular_products = popular_salesperson_products(emp)
        return render_template('salesperson_dashboard.html',
                               products=popular_products)
    else:
        direct_reports = sorted(emp.direct_reports,
                                key=lambda employee: employee.sales_total)
        low_sales = direct_reports[:3]
        top_sales = reversed(direct_reports[-3:])
        return render_template('manager_dashboard.html',
                               title='Home',
                               low_sales=low_sales,
                               top_sales=top_sales)

def client_dashboard():
    cli = Client.query.filter_by(user_id=current_user.id).first()
    if cli is None:
        abort(404)
    products = popular_customer_products(cli.client_id)
    return render_template('client_dashboard.html',
                           title='Home',
                           products=products)

###############################################################################
# User Management
###############################################################################
@app.route('/users/')
@employees_only(['Director'])
@login_required
def users():
    # TODO: Make only accesible by directors
    userlist = User.query.filter_by(active=True).all()
    return render_template('users.html', title='All Current Users', users=userlist)

@app.route('/users/add/', methods=['GET', 'POST'])
@employees_only(['Director'])
@login_required
def add_user():
    form = CreateUserForm()
    title = 'Add User'

    # Send user back to previous page if form errors exist
    if form.validate_on_submit():
        # Validate form data
        if form.password1.data == form.password2.data:
            user = User()
            user.username = form.username.data
            user.password_hash = unicode(bcrypt.generate_password_hash(form.password1.data))
            user.active = True
            user.is_employee = form.is_employee.data
            db.session.add(user)
            db.session.commit()
            flash('User added successfully')
            return redirect('/users/')
        else:
            flash('Passwords do not match')
    return render_template('add_user.html', title=title, form=form)

@app.route('/employee/add/', methods=['GET', 'POST'])
@employees_only(['Director'])
@login_required
def add_employee():
    form = AddEmployeeForm()
    title = 'Add Employee'
    managedBy = [(e.employee_id,e.username) for e in Employee.query.filter(Employee.title != 'Salesperson').all()]
    form.managed_by.choices = managedBy
    # Send user back to previous page if form errors exist
    if form.validate_on_submit():
        # Validate form data
        if form.password1.data == form.password2.data:
            user = Employee()
            user.username = form.username.data
            user.password_hash = unicode(bcrypt.generate_password_hash(form.password1.data))
            user.active = True
	    user.is_employee = True
	    user.managed_by = form.managed_by.data
	    user.title = form.title.data
	    user.commission = form.commission.data
	    user.max_discount = form.max_discount.data
            db.session.add(user)
            db.session.commit()
            flash('Employee added successfully')
            return redirect('/employees/')
        else:
	    flash('Passwords do not match')
    flash_errors(form)
    return render_template('add_employee.html', title=title, form=form)
    

@app.route('/clients/', methods=['GET', 'POST'])
@login_required
@employees_only()
def clients():
    # TODO: Only list clients that are assigned to salesperson or one a
    #       a director/manager manages.
    clients = flatten_hierarchy(current_user.employee,
                                lambda employee: employee.clients)
    title = 'All Clients'
    return render_template('clients.html', title=title, clients=clients)

@app.route('/employees/', methods=['GET', 'POST'])
@login_required
@employees_only()
def employees():
    employees = Employee.query.all()
    title = 'All Employees'
    return render_template('employees.html', title=title, employees=employees)

@app.route('/client/<client_id>/')
@employees_only()
@login_required
def client(client_id):
    # TODO: Only list clients that are assigned to salesperson or one a
    #       a director/manager manages.
    cli = Client.query.filter_by(client_id=client_id).first()
    if cli is None:
        abort(404)
    return render_template('client.html',
                           title = 'Client - %s' % (cli.username),
                           client=cli) 

@app.route('/client/edit/<client_id>/')
@employees_only()
@login_required
def edit_client(client_id):
    # TODO: Only list clients that are assigned to salesperson or one a
    #       a director/manager manages.
    cli = Client.query.filter_by(client_id=client_id).first()
    if cli is None:
        abort(404)
    return render_template('edit_client.html',
                           title = 'Edit Client - %s' % (cli.username),
                           client=cli) 



@app.route('/client/add/', methods=['GET', 'POST'])
@employees_only(['Director']) # TODO: should managers be able to do this?
@login_required
def add_client():
    form = AddClientForm()
    all_reports = flatten_hierarchy(current_user.employee, lambda e: [e])
    salesperson_ids = [(s.employee_id, s.username) for s in all_reports if s.title == 'Salesperson'] 
    form.salesperson_id.choices = salesperson_ids
    if form.validate_on_submit():
        cli = Client()
        cli.username = form.username.data
        cli.password_hash = unicode(bcrypt.generate_password_hash(form.password1.data))
        cli.active = True
        cli.is_employee = False
        cli.company = form.company.data
        cli.salesperson_id = form.salesperson_id.data
        db.session.add(cli)
        db.session.commit()
        flash('Client added successfully')
        return redirect(url_for('clients'))
    flash_errors(form)
    return render_template('add_client.html', title='Add Client', form=form)

    

@app.route('/employee/<employee_id>/')
@employees_only()
@login_required
def employee(employee_id):
    # TODO: Only list employees that are managed by that employee.
    emp = Employee.query.filter_by(employee_id=employee_id).first()
    if emp is None:
        abort(404)
    return render_template('employee.html',
                           title = 'Employee - %s' % (emp.username),
                           employee=emp) 

@app.route('/employee/edit/<employee_id>/')
@employees_only()
@login_required
def edit_employee(employee_id):
    # TODO: Only list employees that are managed by that employee.
    emp = Employee.query.filter_by(employee_id=employee_id).first()
    if emp is None:
        abort(404)
    return render_template('edit_employee.html',
                           title = 'Edit Employee - %s' % (emp.username),
                           employee=emp) 
###############################################################################
# Employee sales and orders 
###############################################################################
@app.route('/sales/')
@employees_only()
@login_required
def sales():
    # TODO: Needs QA - particularly worried about getting all sales in a
    # management hierarchy
    emp = current_user.employee
    order_ids = flatten_hierarchy(emp,
                                  lambda e: [order.id for order in e.orders])
    orders = Order.query.filter(Order.id.in_(tuple(order_ids))).all()
    return render_template('sales.html',
                           title='Sales',
                           orders=orders)

###############################################################################
# Products / Inventory 
###############################################################################
@app.route('/products/')
@login_required
def products():
    if current_user.is_employee:
        return employee_products()
    return client_products()

def employee_products():
    emp = Employee.query.filter_by(user_id=current_user.id).first()
    if emp is None:
        abort(503)
    all_products = Product.query.all()
    if emp.title == 'Director':
        products = all_products
    else:
        products = [p for p in all_products if p.active]
    return render_template('employee_products.html',
                           title='Products',
                           employee=emp,
                           products=products)
def client_products():
    cli = Client.query.filter_by(user_id=current_user.id).first()
    if cli is None:
        abort(503)
    products = Product.query.filter_by(active=True).all()
    return render_template('client_products.html',
                           title='Products',
                           products=products)

@app.route('/product/reorder/<int:product_id>/', methods=['GET', 'POST'])
@login_required
@employees_only(['Director'])
def reorder_product(product_id):
    product = Product.query.filter_by(id=product_id).filter_by(active=True).first()
    if product is None:
        abort(404)
    form = ReorderProductForm(obj=product, exclude='active')
    if form.validate_on_submit():
        new_quantity = form.quantity.data
        if new_quantity < product.quantity:
            flash('New quantity must be greater than current quantity')
        else:
            product.quantity = new_quantity
            db.session.commit()
            flash('Product quantity updated')
            return redirect(url_for('products'))
    flash_errors(form)
    return render_template('reorder_product.html',
                           title='Reorder %s' % (product.name),
                           form=form,
                           product=product)

@employees_only(['Director'])
@login_required
@app.route('/products/add/', methods=['GET', 'POST'])
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(manufacturer=form.manufacturer.data,
                          name=form.name.data,
                          price=form.price.data,
                          quantity=form.quantity.data,
                          active=True)
        db.session.add(product)
        db.session.commit()
        flash('Product added')
        return redirect(url_for('products'))

    flash_errors(form)
    return render_template('add_product.html',
                           title='Add Product',
                           form=form)
###############################################################################
# Demo screens
###############################################################################
from collections import defaultdict

def popular_customer_products(customer_id):
    all_counter = defaultdict(int)
    cust_counter = defaultdict(int)
    for item in OrderItem.query.all():
        if item.product.active:
            all_counter[item.product_id] += item.quantity
            if item.order and item.order.client == customer_id:
                cust_counter[item.product_id] += item.quantity

    if len(cust_counter) >= 3:
       counter = cust_counter
    else:
       counter = all_counter

    product_ids = [k for (k, v) in sorted(counter.items(), key=lambda (k, v): v)][:3]
    return [p for p in Product.query.all() if p.id in product_ids]

def popular_salesperson_products(employee):
    counter = defaultdict(int) 
    for order in employee.orders:
        for item in order.items:
            if item.product.active:
                counter[item.product.id] += item.quantity
    popular = sorted(counter.keys(), 
                     key=lambda item_id: counter[item_id],
                     reverse=True)[:3]
    return Product.query.filter(Product.id.in_(tuple(popular))).all()

@app.route('/demo/buy/')
def buy():
    products = Product.query.filter_by(active=True).all()
    return render_template('demo_buy.html', title='All Products', products=products)


@app.route('/demo/buy/<int:product_id>/', methods=['GET', 'POST'])
def buy_product(product_id):
    matching_products = Product.query.filter_by(id=product_id, active=True).all()
    if len(matching_products) == 0:
        flash('No matching product found')
        return redirect('/demo/buy/')

    product = matching_products.pop()
    if request.method == 'GET':
        form = ProductForm(obj=product, exclude='active')
        print 'GET', form.data
        return render_template('demo_buy_product.html',
                               title='Buy %s' % (product.name),
                               form=form)
    form = ProductForm(exclude='active')
    form.active.data = product.active
    print 'POST', form.data
    if form.validate():
        print product.id, type(product.id)
        print form.quantity.data, type(form.quantity.data)
        add_to_cart(product, form.quantity.data)
        flash('%s - %s has been added to your cart' % (product.manufacturer,
                                                       product.name))
        return redirect('/demo/cart/')
    else:
        print form.errors
        flash('%s - %s could not be added to your cart' % (product.manufacturer,
                                                           product.name))
        return render_template('demo_buy_product.html',
                               title='Buy %s' % (product.name),
                               form=form)


@app.route('/demo/cart/')
def cart():
    cart = [] 
    if 'cart' in session:
        cart = [(p, session['cart'][unicode(p.id)]) for p in Product.query.all() if unicode(p.id) in session['cart']]
    return render_template('demo_cart.html',
                           title='Your Cart',
                           cart=cart)

@app.route('/demo/cart/placeorder/')
def place_order():
    order_id = max(db.session.query(Order.id).all())[0] + 1
    timestamp = timestamp=datetime.datetime.now()
    db.session.add(Order(id=order_id, timestamp=timestamp,
                         client=1, salesperson=2, commission=0.05))
    for product_id, quantity in session['cart'].items():
        product = db.session.query(Product).filter_by(id=int(product_id)).first()
        db.session.add(OrderItem(order_id=order_id,
                                 product_id=product.id,
                                 price=product.price,
                                 quantity=int(quantity)))
    db.session.commit()
    flash('Order submitted at %s' % (timestamp.strftime('%Y-%m-%d %H:%M:%S')))
    session['cart'] = {}
    return redirect('/demo/orders/customer/')

@app.route('/demo/orders/customer/')
def orders():
    matching_orders = sorted(Order.query.filter_by(client=1),
                             key=lambda order: order.timestamp,
                             reverse=True)
    return render_template('demo_customer_orders.html',
                           title='All Orders',
                           orders=matching_orders)

@app.route('/demo/orders/customer/<int:order_id>/')
def order(order_id):
    items = OrderItem.query.filter_by(order_id=order_id).all() 
    print items
    return render_template('demo_customer_order_items.html',
                           title='Order Details',
                           items=items)



def add_to_cart(product, quantity):
    if 'cart' not in session:
        session['cart'] = {}
    session['cart'][unicode(product.id)] = unicode(quantity)

def remove_from_cart(product):
    add_to_cart(product, 0)
