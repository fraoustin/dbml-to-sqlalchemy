import unittest
import sqlalchemy as db
import sqlalchemy.sql.sqltypes
import sqlalchemy.exc
from sqlalchemy.orm import Session
from pydbml import PyDBML

from dbml_to_sqlalchemy import createModel


class BasicTest(unittest.TestCase):
    """
        Class for Basic Unitaire Test for dbml_to_sqlalchemy
    """
    def setUp(self):
        database_file = "sqlite://"
        self.engine = db.create_engine(database_file, echo=False)
        self.conn = self.engine.connect()
        self.metadata = db.MetaData()

        try:
            from sqlalchemy.orm import DeclarativeBase

            class Base(DeclarativeBase):
                metadata = self.metadata
        except Exception:
            # for sqlalchemy 1.4
            from sqlalchemy.orm import declarative_base
            Base = declarative_base()
        self.Base = Base

    def test_basic(self):
        with Session(self.engine) as session:
            source = """
            Table user {
            id integer [primary key]
            }
            """
            parsed = PyDBML(source)
            User = createModel(parsed.tables[0], self.Base)
            self.assertEqual("User", User.__name__)
            self.assertEqual("user", User.__tablename__)
            self.assertTrue("id" in dir(User))
            self.assertEqual(User.id.type.__class__, sqlalchemy.sql.sqltypes.Integer)
            self.assertTrue(User.id.primary_key)
            self.metadata.create_all(self.engine)
            user = User(id=1)
            session.add_all([user, ])
            session.commit()
            self.assertEqual(session.scalars(db.select(User)).all()[0].id, 1)

    def test_typ_columns(self):
        with Session(self.engine):
            source = """
            Table user {
            id integer [primary key]
            cola varchar
            colb varchar(20)
            colc decimal(10,2)
            cold blob
            cole unknown
            }
            """
            parsed = PyDBML(source)
            User = createModel(parsed.tables[0], self.Base)
            self.assertEqual(User.id.type.__class__, sqlalchemy.sql.sqltypes.Integer)
            self.assertTrue(User.id.primary_key)
            self.assertEqual(User.cola.type.__class__, sqlalchemy.sql.sqltypes.VARCHAR)
            self.assertEqual(User.colb.type.__class__, sqlalchemy.sql.sqltypes.VARCHAR)
            self.assertEqual(User.colb.type.length, 20)
            self.assertEqual(User.colc.type.__class__, sqlalchemy.sql.sqltypes.DECIMAL)
            self.assertEqual(User.colc.type.precision, 10)
            self.assertEqual(User.colc.type.scale, 2)
            self.assertEqual(User.cold.type.__class__, sqlalchemy.sql.sqltypes.BLOB)
            self.assertEqual(User.cole.type.__class__, sqlalchemy.sql.sqltypes.String)

    def test_null_columns(self):
        with Session(self.engine) as session:
            source = """
            Table user {
            id integer [primary key]
            cola varchar [not null]
            colb varchar
            }
            """
            parsed = PyDBML(source)
            User = createModel(parsed.tables[0], self.Base)
            self.assertEqual(User.cola.nullable, False)
            self.assertEqual(User.colb.nullable, True)
            self.metadata.create_all(self.engine)
            user = User(id=1, cola='test', colb='test')
            session.add_all([user, ])
            self.assertEqual(session.commit(), None)
            user = User(id=2, cola='test', colb=None)
            session.add_all([user, ])
            self.assertEqual(session.commit(), None)
            with self.assertRaises(sqlalchemy.exc.IntegrityError):
                user = User(id=3, cola=None, colb='test')
                session.add_all([user, ])
                session.commit()

    def test_unique_columns(self):
        with Session(self.engine) as session:
            source = """
            Table user {
            id integer [primary key]
            cola varchar [unique]
            colb varchar
            }
            """
            parsed = PyDBML(source)
            User = createModel(parsed.tables[0], self.Base)
            self.assertEqual(User.cola.unique, True)
            self.assertEqual(User.colb.unique, False)
            self.metadata.create_all(self.engine)
            user = User(id=1, cola='test', colb='test')
            session.add_all([user, ])
            self.assertEqual(session.commit(), None)
            user = User(id=2, cola='test2', colb='test')
            session.add_all([user, ])
            self.assertEqual(session.commit(), None)
            with self.assertRaises(sqlalchemy.exc.IntegrityError):
                user = User(id=3, cola='test2', colb=None)
                session.add_all([user, ])
                session.commit()

    def test_default_columns(self):
        with Session(self.engine) as session:
            source = """
            Table user {
            id integer [primary key]
            cola varchar [default: "coucou"]
            colb boolean [default: True]
            colc integer [default: 2]
            }
            """
            parsed = PyDBML(source)
            User = createModel(parsed.tables[0], self.Base)
            self.metadata.create_all(self.engine)
            user = User(id=1, cola=None)
            session.add_all([user, ])
            session.commit()
            self.assertEqual(session.scalars(db.select(User)).all()[0].cola, "coucou")
            self.assertEqual(session.scalars(db.select(User)).all()[0].colb, True)
            self.assertEqual(session.scalars(db.select(User)).all()[0].colc, 2)

    def test_enum_columns(self):
        with Session(self.engine) as session:
            source = """
            Table user {
            id integer [primary key]
            cola job_status
            }

            enum job_status {
                created [note: 'Waiting to be processed']
                running
                done
                failure
            }
            """
            parsed = PyDBML(source)
            User = createModel(parsed.tables[0], self.Base)
            self.metadata.create_all(self.engine)
            user = User(id=1, cola=None)
            session.add_all([user, ])
            session.commit()
            self.assertEqual(session.scalars(db.select(User)).all()[0].cola, None)
            user = User(id=2, cola='running')
            session.add_all([user, ])
            session.commit()
            self.assertEqual(session.scalars(db.select(User)).all()[1].cola.name, "running")
            with self.assertRaises(sqlalchemy.exc.IntegrityError):
                user = User(id=3, cola="wrong_value")
                session.add_all([user, ])
                session.commit()

    def test_autoincrement_columns(self):
        with Session(self.engine) as session:
            source = """
            Table user {
            id integer [primary key, increment]
            }
            """
            parsed = PyDBML(source)
            User = createModel(parsed.tables[0], self.Base)
            self.metadata.create_all(self.engine)
            user = User()
            session.add_all([user, ])
            session.commit()
            self.assertEqual(session.scalars(db.select(User)).all()[0].id, 1)
            user = User()
            session.add_all([user, ])
            session.commit()
            self.assertEqual(session.scalars(db.select(User)).all()[1].id, 2)

    def test_pk_multiple(self):
        with Session(self.engine) as session:
            source = """
            Table user {
            id integer
            idd integer

            indexes {
                (id, idd) [pk]
            }
            }
            """
            parsed = PyDBML(source)
            User = createModel(parsed.tables[0], self.Base)
            self.metadata.create_all(self.engine)
            user = User(id=1, idd=1)
            session.add_all([user, ])
            session.commit()
            self.assertEqual(session.scalars(db.select(User)).all()[-1].id, 1)
            user = User(id=1, idd=2)
            session.add_all([user, ])
            session.commit()
            self.assertEqual(session.scalars(db.select(User)).all()[-1].id, 1)
            user = User(id=2, idd=2)
            session.add_all([user, ])
            session.commit()
            self.assertEqual(session.scalars(db.select(User)).all()[-1].id, 2)
            with self.assertRaises(sqlalchemy.exc.IntegrityError):
                user = User(id=2, idd=2)
                session.add_all([user, ])
                session.commit()

    def test_unique_multiple(self):
        with Session(self.engine) as session:
            source = """
            Table user {
            id integer [pk, increment]
            idd integer
            iddd integer

            indexes {
                (idd, iddd) [unique]
            }
            }
            """
            parsed = PyDBML(source)
            User = createModel(parsed.tables[0], self.Base)
            self.metadata.create_all(self.engine)
            user = User(idd=1, iddd=1)
            session.add_all([user, ])
            session.commit()
            self.assertEqual(session.scalars(db.select(User)).all()[-1].idd, 1)
            user = User(idd=1, iddd=2)
            session.add_all([user, ])
            session.commit()
            self.assertEqual(session.scalars(db.select(User)).all()[-1].idd, 1)
            user = User(idd=2, iddd=2)
            session.add_all([user, ])
            session.commit()
            self.assertEqual(session.scalars(db.select(User)).all()[-1].idd, 2)
            with self.assertRaises(sqlalchemy.exc.IntegrityError):
                user = User(idd=2, iddd=2)
                session.add_all([user, ])
                session.commit()
