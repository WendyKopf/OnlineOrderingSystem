from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True)
    password_hash = db.Column(db.Binary(60))

    def __repr__(self):
        return '<User %r ID: %i>' % (self.username, self.id)
