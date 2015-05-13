import datetime
from functools import wraps

from flask import abort, flash, g, redirect, render_template, request, session, url_for
from flask.ext.login import current_user, login_required, login_user, logout_user

from app import app, bcrypt, db, login_manager

from .forms import (
    ClientForm, CreateUserForm, EmployeeForm, LoginForm, ProductForm,
    ReorderProductForm
)
from .models import Client, Employee, Product, Order, OrderItem, User

from helpers import add_error


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
        return render_template('salesperson_dashboard.html')
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
    products = popular_products(cli.client_id)
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


@app.route('/clients/', methods=['GET', 'POST'])
@login_required
@employees_only()
def clients():
    # TODO: Only list clients that are assigned to salesperson or one a
    #       a director/manager manages.
    title = 'All Clients'
    return render_template('clients.html', title=title)

@app.route('/client/<user_id>/')
@employees_only()
@login_required
def client(user_id):
    # TODO: Only list clients that are assigned to salesperson or one a
    #       a director/manager manages.
    cli = Client.query.filter_by(user_id=user_id).first()
    if cli is None:
        abort(404)
    return render_template('client.html',
                           title = 'Client - %s' % (cli.username),
                           client=cli) 
    

@app.route('/employee/<user_id>/')
@employees_only()
@login_required
def employee(user_id):
    # TODO: Only list employees that are managed by that employee.
    emp = Employee.query.filter_by(user_id=user_id).first()
    if emp is None:
        abort(404)
    return render_template('employee.html',
                           title = 'Employee - %s' % (emp.username),
                           employee=emp) 

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
    return render_template('reorder_product.html',
                           title='Reorder %s' % (product.name),
                           form=form,
                           product=product)

###############################################################################
# Demo screens
###############################################################################
from collections import defaultdict

def popular_products(customer_id):
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
