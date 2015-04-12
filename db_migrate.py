#!/usr/bin/env python
import imp
from migrate.versioning import api

from app import db
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO

# Construct filename of new migration script
vsn = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
new_vsn = vsn + 1
migration = '%s/versions/%03d_migration.py' % (SQLALCHEMY_MIGRATE_REPO, new_vsn)

# Generate code for migration script
tmp_module = imp.new_module('old_module')
old_model = api.create_model(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
exec(old_model, tmp_module.__dict__)
script = api.make_update_script_for_model(SQLALCHEMY_DATABASE_URI,
                                          SQLALCHEMY_MIGRATE_REPO,
                                          tmp_module.meta,
                                          db.metadata)

# Write script contents
with open(migration, 'wt') as fout:
    fout.write(script)

# Do the upgrade
api.upgrade(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
upgrade_vsn = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)

print 'New migration saved at', migration
print 'Current DB version', upgrade_vsn

