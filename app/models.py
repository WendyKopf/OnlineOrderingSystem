from app import db

USERNAME_LEN = 32

class User(db.Model):
    username = db.Column(db.String(USERNAME_LEN), primary_key=True)
    password_hash = db.Column(db.Binary(60), nullable=False)
    is_employee = db.Column(db.Boolean, nullable=False)

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
    role = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)

    def __repr__(self):
        return '<Employee id: %i, username: %r>' % (self.id, self.username)

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, unique=True)

    def __repr__(self):
        return '<Role id: %i, name: %r>' % (self.id, self.name)
