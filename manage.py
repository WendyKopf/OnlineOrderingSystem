#!/usr/bin/env python
from flask.ext.script import Command, Manager, Shell

from app import app, bcrypt, db, forms, models

manager = Manager(app)
def _make_context():
    return dict(app=app, forms=forms, db=db, models=models)

class CreateAdminScript(Command):
    def run(self):
        import getpass

        # Get username from command line
        while True:
            username = raw_input("\nUsername: ")
            if not models.USERNAME_MIN_LEN <= len(username) <= models.USERNAME_MAX_LEN:
                print 'Username must be between %i and %i characters long\n' % (models.USERNAME_MIN_LEN,
                                                                              models.USERNAME_MAX_LEN)
            else:
                break

        # Get password from command line
        while True:
            password = getpass.getpass("Enter password: ")
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                print 'Passwords do not match!\n'
            elif len(password) < models.PASSWORD_MIN_LEN:
                print 'Password must be between at least %i characters long\n' % (models.PASSWORD_MIN_LEN)
            else:
                break

        # Hash password
        password_hash = bcrypt.generate_password_hash(password)

        # Attempt to save in DB
        user = models.User(username=username,
                           password_hash=password_hash,
                           active=True, is_employee=True)
        employee = models.Employee(username=username,
                                   managed_by=None,
                                   commission=models.DEFAULT_DIRECTOR_COMMISSION,
                                   max_discount=models.DEFAULT_DIRECTOR_MAX_DISCOUNT,
                                   title='Director')
        db.session.add(user)
        db.session.add(employee)
        db.session.commit()

        print 'Admin added'


manager = Manager(app)
manager.add_command("shell", Shell(make_context=_make_context))
manager.add_command("createadmin", CreateAdminScript())

if __name__ == "__main__":
    manager.run()
