from app import db

USERNAME_MIN_LEN = 3
USERNAME_MAX_LEN = 32
PASSWORD_MIN_LEN = 10

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(USERNAME_MAX_LEN), unique=True)
    password_hash = db.Column(db.Binary(60), nullable=False)
    is_employee = db.Column(db.Boolean, nullable=False)
    active = db.Column(db.Boolean, nullable=False)

    _authenticated = False 

    def get_id(self):
        return self.username
    def is_active(self):
        return self.active
    def is_anonymous(self):
        return False
    def is_authenticated(self):
        return True
    @property
    def client(self):
        if self.is_employee:
            return None
        return Client.query.filter_by(user_id=self.id).first()
    @property
    def employee(self):
        if self.is_employee:
            return Employee.query.filter_by(user_id=self.id).first()
        return None
    def employee_title(self):
        if self.is_employee:
            return Employee.query.filter_by(user_id=self.id).first().title
        return None
    def __repr__(self):
        return '<User %r>' % (self.username)

class Client(User):
    __tablename__ = 'client'
    client_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer,
                        db.ForeignKey('user.id'),
                        nullable=False,
                        unique=True)
    company = db.Column(db.String(64), nullable=False)
    salesperson_id = db.Column(db.Integer, db.ForeignKey('employee.employee_id'))

    def __repr__(self):
        return '<Client id: %i, username: %r>' % (self.id, self.username)

# XXX Should these be in the DB instead?
DEFAULT_DIRECTOR_COMMISSION     = 0.05
DEFAULT_DIRECTOR_MAX_DISCOUNT   = 0.20

class Employee(User):
    __tablename__ = 'employee'
    employee_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer,
                        db.ForeignKey('user.id'),
                        nullable=False,
                        unique=True)
    managed_by = db.Column(db.Integer, db.ForeignKey('employee.employee_id'), nullable=True)
    commission = db.Column(db.Float, nullable=False)
    max_discount = db.Column(db.Float, nullable=False)
    title = db.Column(db.Enum('Director', 'Manager', 'Salesperson'), nullable=False)

    manager = db.relation('Employee',
                          foreign_keys=[managed_by],
                          remote_side=[employee_id],
                          backref=db.backref('direct_reports'))
    clients = db.relation('Client', foreign_keys=[Client.salesperson_id],
                          backref=db.backref('salesperson'))

    @property
    def sales_total(self):
        return sum([order.total for order in self.orders])
    @property
    def all_reports(self):
        reports = [r for r in self.direct_reports]
        for r in reports:
            reports.extend(r.all_reports)
        return reports

    def __repr__(self):
        return '<Employee id: %i, username: %r>' % (self.id, self.username)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    manufacturer = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    active = db.Column(db.Boolean, nullable=False)

    @property
    def promo_price(self):
        promo = Promotion.query.filter_by(product_id=self.id).first()
        if promo is None:
            return self.price
        return promo.discount
    @property
    def description(self):
        return '%s - %s' % (self.manufacturer, self.name)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    client = db.Column(db.Integer, db.ForeignKey('client.client_id'), nullable=False)
    salesperson = db.Column(db.Integer, db.ForeignKey('employee.employee_id'), nullable=False)
    commission = db.Column(db.Float, nullable=False)

    sold_by = db.relationship('Employee', backref=db.backref('orders', lazy='dynamic'))
    sold_to = db.relationship('Client', backref=db.backref('orders', lazy='dynamic'))

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
    product = db.relationship('Product')

class Feedback(db.Model):
    from_user = db.Column(db.String(USERNAME_MAX_LEN), nullable=False, primary_key=True)
    to_user = db.Column(db.String(USERNAME_MAX_LEN), nullable=False, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, primary_key=True)
    is_positive = db.Column(db.Boolean, nullable=False)
