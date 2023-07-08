import unittest
from flask import Flask, request, json
from pydbml import PyDBML

from flask_sqlalchemy import SQLAlchemy
from dbml_to_sqlalchemy import createModel


class BasicTest(unittest.TestCase):
    """
        Class for Basic Unitaire Test for flask_sqlalchemy_api
    """
    def setUp(self):
        self.app = Flask(__name__)
        self.app.testing = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
        self.db = SQLAlchemy()

        self.db.init_app(self.app)

    def test_create_insert(self):
        with self.app.test_client():
            source = """
            Table user {
            id integer [primary key]
            }
            """
            parsed = PyDBML(source)
            User = createModel(parsed.tables[0], self.db.Model)
            with self.app.app_context():
                self.db.drop_all()
                self.db.create_all()
                item = User(id=1)
                self.db.session.add(item)
                self.db.session.commit()
                self.assertEqual(User.query.all()[0].id, 1)
