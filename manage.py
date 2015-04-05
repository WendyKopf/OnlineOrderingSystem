from flask.ext.script import Shell, Manager

from app import app, forms

manager = Manager(app)
def _make_context():
    return dict(app=app, forms=forms, db=None, models=None)

manager = Manager(app)
manager.add_command("shell", Shell(make_context=_make_context))

if __name__ == "__main__":
    manager.run()
