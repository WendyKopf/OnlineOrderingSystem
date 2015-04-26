from flask import flash, redirect, render_template, request, session, url_for

from app import app, db

from .forms import CreateLoginForm, ProductForm
from .models import Employee, Product, Order, OrderItem

from helpers import add_error

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

@app.route('/clients/add/', methods=['GET', 'POST'])
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

@app.route('/clients/', methods=['GET', 'POST'])
def clients():
    title = 'All Clients'
    return render_template('clients.html', title=title)


###############################################################################
# Demo screens
###############################################################################
import datetime
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

@app.route('/')
@app.route('/demo/dashboard/customer/')
def customer_dashboard():
    products = popular_products(1)
    return render_template('demo_customer_dashboard.html',
                           title='Home',
                           products=products)

@app.route('/demo/dashboard/manager/')
def manager_dashboard():
    direct_reports = sorted(Employee.query.filter_by(id=1).first().direct_reports,
                            key=lambda employee: employee.sales_total)
    print [(e.username, e.sales_total) for e in direct_reports]
    low_sales = direct_reports[:3]
    top_sales = reversed(direct_reports[-3:])

    return render_template('demo_manager_dashboard.html',
                           title='Home',
                           low_sales=low_sales,
                           top_sales=top_sales)

def add_to_cart(product, quantity):
    if 'cart' not in session:
        session['cart'] = {}
    session['cart'][unicode(product.id)] = unicode(quantity)

def remove_from_cart(product):
    add_to_cart(product, 0)
