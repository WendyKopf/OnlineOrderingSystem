from app import db

USERNAME_LEN = 32

class User(db.Model):
    username = db.Column(db.String(USERNAME_LEN), primary_key=True)
    password_hash = db.Column(db.Binary(60), nullable=False)
    is_employee = db.Column(db.Boolean, nullable=False)
    active = db.Column(db.Boolean, nullable=False)

    def __repr__(self):
        return '<User %r>' % (self.username)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(USERNAME_LEN), db.ForeignKey('user.username'), nullable=False, unique=True)
    company = db.Column(db.String(64), nullable=False)

    def __repr__(self):
        return '<Client id: %i, username: %r>' % (self.id, self.username)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(USERNAME_LEN), db.ForeignKey('user.username'), nullable=False, unique=True)
    managed_by = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    commission = db.Column(db.Float, nullable=False)
    max_discount = db.Column(db.Float, nullable=False)
    title = db.Column(db.Enum('Director', 'Manager', 'Salesperson'), nullable=False)

    manager = db.relation('Employee', remote_side=[id], backref=db.backref('direct_reports'))

    @property
    def sales_total(self):
        return sum([order.total for order in self.orders])
    def __repr__(self):
        return '<Employee id: %i, username: %r>' % (self.id, self.username)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    manufacturer = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    active = db.Column(db.Boolean, nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    client = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    salesperson = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    commission = db.Column(db.Float, nullable=False)

    _sold_by = db.relationship('Employee', backref=db.backref('orders', lazy='dynamic'))

    @property
    def total(self):
        return sum([item.price * item.quantity for item in self.items]) 

class OrderItem(db.Model):
    order_id = db.Column(db.Integer,  db.ForeignKey('order.id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    order = db.relationship('Order', backref=db.backref('items', lazy='dynamic'))
    product = db.relationship('Product')

class Promotion(db.Model):
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    discount = db.Column(db.Float, nullable=False, unique=True)

class Feedback(db.Model):
    from_user = db.Column(db.String(USERNAME_LEN), nullable=False, primary_key=True)
    to_user = db.Column(db.String(USERNAME_LEN), nullable=False, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, primary_key=True)
    is_positive = db.Column(db.Boolean, nullable=False)
