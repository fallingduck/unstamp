import os
from peewee import SqliteDatabase, Model, PrimaryKeyField, CharField


if not os.path.exists('./.data'):
    os.mkdir('./.data')

_email_db = SqliteDatabase('./.data/email.db')


class Address(Model):
    id_ = PrimaryKeyField()
    email = CharField(unique=True)
    password = CharField()
    forward_to = CharField()

    class Meta:
        database = _email_db


_email_db.connect()

Address.create_table(True)
