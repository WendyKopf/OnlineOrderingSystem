import datetime
from functools import wraps
from collections import defaultdict

from flask import abort, flash, g, redirect, render_template, request, session, url_for
from flask.ext.login import current_user, login_required, login_user, logout_user

from app import app, bcrypt, db, login_manager

from .forms import (
    AddClientForm, AddEmployeeForm, ClientForm, CreateUserForm, EmployeeForm, LoginForm,
    OrderForm, ProductForm, PromotionForm, ReorderProductForm, IntegerField
)
from .models import Client, Employee, Feedback, Product, Promotion, Order, OrderItem, User

from helpers import add_error, flash_errors, flash_form_errors, flatten_hierarchy


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
        try:
            if bcrypt.check_password_hash(saved_hash, form.password.data):
                current_user._authenticated = True
                login_user(user, remember=True)
                return redirect(request.args.get('next') or url_for('dashboard'))
        except:
            pass
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
# Employee Management
###############################################################################
@app.route('/employees/')
@login_required
@employees_only(['Manager', 'Director'])
def employees():
    employees = current_user.employee.all_reports
    title = 'All Employees'
    return render_template('employees.html', title=title, employees=employees)

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

@app.route('/employee/add/', methods=['GET', 'POST'])
@employees_only(['Manager', 'Director'])
@login_required
def add_employee():
    form = AddEmployeeForm()
    title = 'Add Employee'
    if current_user.employee.title == 'Manager':
        form.managed_by.choices = [(current_user.employee.employee_id, current_user.employee.username)]
        form.title.choices = [('Salesperson', 'Salesperson')]
    else:
        managedBy = [(e.employee_id, e.username) for e in Employee.query.filter(Employee.title != 'Salesperson').all()]
        form.managed_by.choices = managedBy

    # Send user back to previous page if form errors exist
    if form.validate_on_submit():
        # Validate form data
        manager = Employee.query.filter_by(employee_id=form.managed_by.data).first()
        if form.password1.data != form.password2.data:
            flash('Passwords do not match')
        elif form.title.data == 'Director' and manager.title is not None:
            flash('Directors cannot have a manager')
        elif form.title.data == 'Manager' and manager.title != 'Director':
            flash('A Manager must be managed by a Director')
        elif form.title.data == 'Salesperson' and manager.title != 'Manager':
            flash('A Salesperson must be managed by a Manager')
        else:
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
    flash_form_errors(form)
    return render_template('add_employee.html', title=title, form=form)
    
###############################################################################
# Client Management
###############################################################################
@app.route('/clients/', methods=['GET', 'POST'])
@login_required
@employees_only()
def clients():
    clients = flatten_hierarchy(current_user.employee,
                                lambda employee: employee.clients)
    title = 'All Clients'
    return render_template('clients.html', title=title, clients=clients)

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

@app.route('/client/add/', methods=['GET', 'POST'])
@employees_only(['Manager'])
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
    flash_form_errors(form)
    return render_template('add_client.html', title='Add Client', form=form)

    

###############################################################################
# Employee sales and orders 
###############################################################################
@app.route('/sales/')
@employees_only()
@login_required
def sales():
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
    flash_form_errors(form)
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

    flash_form_errors(form)
    return render_template('add_product.html',
                           title='Add Product',
                           form=form)
###############################################################################
# Promotions
###############################################################################
@employees_only()
@login_required
@app.route('/promotions/')
def promotions():
    promotions = Promotion.query.all()
    return render_template('promotions.html',
                           title='All Promotions',
                           promotions=promotions)

@employees_only(['Manager'])
@login_required
@app.route('/promotions/add/')
def select_add_promotion():
    all_products = Product.query.filter_by(active=True).all()
    promoted_products = [p.product for p in Promotion.query.all()]
    products = [p for p in all_products if p not in promoted_products]
    return render_template('select_add_promotion.html',
                           title='Select Product',
                           products=products)

@employees_only(['Manager'])
@login_required
@app.route('/promotions/add/<int:product_id>/', methods=['GET', 'POST'])
@app.route('/promotions/edit/<int:product_id>/', methods=['GET', 'POST'])
def add_promotion(product_id):
    form = PromotionForm()
    product = Product.query.filter_by(id=product_id).first()
    current_promotion = Promotion.query.filter_by(product_id=product.id).first()
    if product is None:
        abort(404)
    if form.validate_on_submit():
        discount = float(form.discount.data)
        if discount > product.price:
            flash('Discount price cannot be greater than list price')
        elif discount <= 0:
            flash('Discount price must be at least $0.01')
        else:
            if current_promotion is None:
                current_promotion = Promotion()
                current_promotion.product_id = product_id
                current_promotion.discount = discount
                db.session.add(current_promotion)
            else:
                current_promotion.discount = discount
            db.session.commit()
            flash('Promotion updated')
            return redirect(url_for('promotions'))
    flash_form_errors(form)
    return render_template('add_promotion.html',
                           title='Promotion for %s - %s' % (product.manufacturer, product.name),
                           product=product,
                           current_promotion=current_promotion,
                           form=form)

@employees_only(['Manager'])
@login_required
@app.route('/promotions/delete/<int:product_id>/', methods=['GET', 'POST'])
def delete_promotion(product_id):
    promo = Promotion.query.filter_by(product_id=product_id).first()
    if promo is None:
        abort(404)
    db.session.delete(promo)
    db.session.commit()
    flash('Promotion deleted')
    return redirect(url_for('promotions'))

###############################################################################
# Orders 
###############################################################################
@login_required
@app.route('/orders/')
def orders():
    if current_user.is_employee:
        return employee_orders(current_user.employee)
    return client_orders(current_user.client)

def client_orders(client):
    order_list = client.orders
    return render_template('client_orders.html',
                           title='All Orders',
                           orders=order_list)

def employee_orders(employee):
    if employee.title == 'Salesperson':
        order_list = employee.orders 
    else:
        order_list = flatten_hierarchy(employee, lambda e: e.orders)
    return render_template('employee_orders.html',
                           title='All Orders',
                           orders=order_list)

@login_required
@app.route('/orders/<int:order_id>/')
def view_order(order_id):
    if current_user.is_employee:
        return view_employee_order(current_user.employee, order_id)
    return view_client_order(current_user.client, order_id)

def view_employee_order(employee, order_id):
    all_orders = flatten_hierarchy(employee, lambda e: e.orders)
    matches = [order for order in all_orders if order.id == order_id]
    if matches == []:
        abort(404)
    order = matches[0]
    return render_template('employee_view_order.html',
                           title='Order Details',
                           order=order)

def view_client_order(client, order_id):
    order = Order.query.filter(Order.id==order_id).filter(Order.client==client.client_id).first()
    if order is None:
        abort(404)
    return render_template('client_view_order.html',
                           title='Order Details',
                           order=order)

@employees_only(['Salesperson'])
@login_required
@app.route('/orders/add/<int:client_id>/', methods=['GET', 'POST'])
def add_order(client_id):
    emp_id = current_user.employee.employee_id
    client = Client.query.filter_by(client_id=client_id, salesperson_id=emp_id).first()
    if client is None:
        abort(404)

    class ThisOrderForm(OrderForm): pass
    products = Product.query.filter_by(active=True).filter(Product.quantity>0).all()
    for product in products:
        setattr(ThisOrderForm, str(product.id) + '_quantity', IntegerField('Item Quantity'))
        setattr(ThisOrderForm, str(product.id) + '_discount', IntegerField('Item Discount'))
    form = ThisOrderForm()
    errors = defaultdict(list)
    if form.validate_on_submit():
        try:
            salesperson = current_user.employee
            # Add a new order
            order = Order(timestamp=datetime.datetime.now(),
                          client=client_id,
                          salesperson=salesperson.employee_id,
                          commission=0.0)
                          #commission=current_user.employee.commission)
            db.session.add(order)

            # Update inventory and add order items
            item_count = 0
            for (field, value) in form.data.items():
                if not field.endswith('_quantity'):
                    continue
                id_str, _underscore, _quantity = field.partition('_')
                quantity = value
                if quantity == 0:
                    continue
                if not id_str.isdigit():
                    errors['Form ID'].append('Invalid ID')
                    break
                discount = form.data[id_str + '_discount']
                max_discount = current_user.employee.max_discount
                if discount > max_discount:
                    errors['Discount'].append('Discount cannot exceed %.2f%%' % (max_discount))
                    break
                product_id = int(id_str)
                product = Product.query.filter_by(id=product_id).first()
                if product is None:
                   errors[product.description].append('Invalid Item')
                   break
                if product.quantity < quantity:
                    errors[product.description].append('Insufficent Inventory')
                    break
                product.quantity -= quantity
                price = product.promo_price * ((100 - discount)/100.0)
                db.session.add(OrderItem(order_id=order.id,
                                         product_id=product.id,
                                         price=price,
                                         quantity=quantity))
                order.commission += salesperson.commission * ((100 - discount)/100.0) * price
                item_count += 1

            # Make sure we don't submit an empty order
            if not errors and item_count == 0:
                errors['Quantity'].append('At least one item must be selected')

            # Attempt to commit changes
            if errors:
                db.session.rollback()
            else:
                db.session.commit()
                flash('Order placed')
        except (Exception), err:
            errors['Database'].append(err)
            db.session.rollback()

    flash_errors(errors)
    flash_form_errors(form)
    return render_template('add_order.html',
                           title='Place New Order',
                           client=client,
                           products=products,
                           form=form)
                        
###############################################################################
# Feedback - Likes/Dislikes 
###############################################################################
@login_required
@app.route('/feedback/')
def feedback():
    likes = current_user.likes
    dislikes = current_user.dislikes
    return render_template('feedback.html',
                           title='Feedback',
                           likes=likes,
                           dislikes=dislikes)

@login_required
@employees_only(['Salesperson'])
@app.route('/client/like/<int:client_user_id>/')
def like_client(client_user_id):
    emp = current_user.employee
    client = Client.query.filter_by(user_id=client_user_id, salesperson_id=emp.employee_id).first()
    if client is None:
        abort(404)
    db.session.add(Feedback(from_user=emp.user_id, to_user=client.user_id,
                           timestamp=datetime.datetime.now(), is_positive=True))
    db.session.commit()
    flash('Like added')
    return redirect(url_for('clients'))
                           
@login_required
@employees_only(['Salesperson'])
@app.route('/client/dislike/<int:client_user_id>/')
def dislike_client(client_user_id):
    emp = current_user.employee
    client = Client.query.filter_by(user_id=client_user_id, salesperson_id=emp.employee_id).first()
    if client is None:
        abort(404)
    db.session.add(Feedback(from_user=emp.user_id, to_user=client.user_id,
                           timestamp=datetime.datetime.now(), is_positive=False))
    db.session.commit()
    flash('Disike added')
    return redirect(url_for('clients'))


@login_required
@app.route('/salesperson/like/')
def like_salesperson():
    if current_user.is_employee:
        abort(404)
    client = current_user.client
    db.session.add(Feedback(from_user=client.user_id, to_user=client.salesperson.user_id,
                           timestamp=datetime.datetime.now(), is_positive=True))
    db.session.commit()
    flash('Like added')
    return redirect('/')

@login_required
@app.route('/salesperson/dislike/')
def dislike_salesperson():
    if current_user.is_employee:
        abort(404)
    client = current_user.client
    db.session.add(Feedback(from_user=client.user_id, to_user=client.salesperson.user_id,
                           timestamp=datetime.datetime.now(), is_positive=False))
    db.session.commit()
    flash('Disike added')
    return redirect('/')

###############################################################################
# Popular Products Helpers 
###############################################################################
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

