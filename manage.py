#!/usr/bin/env python
from flask.ext.script import Shell, Manager

from app import app, forms, db, models

manager = Manager(app)
def _make_context():
    return dict(app=app, forms=forms, db=db, models=models)

manager = Manager(app)
manager.add_command("shell", Shell(make_context=_make_context))

if __name__ == "__main__":
    manager.run()
