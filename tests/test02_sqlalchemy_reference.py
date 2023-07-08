import unittest
import sqlalchemy as db
import sqlalchemy.sql.sqltypes
import sqlalchemy.exc
from sqlalchemy.orm import Session
from pydbml import PyDBML

from dbml_to_sqlalchemy import createModel

from sqlalchemy.engine import Engine
from sqlalchemy import event


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


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
            Table usera {
                id integer [pk]
            }

            Table posta {
                id integer [pk]
                userid integer [ref: > usera.id]
            }
            """
            parsed = PyDBML(source)
            User = createModel(parsed.tables[0], self.Base)
            Post = createModel(parsed.tables[1], self.Base)
            self.metadata.create_all(self.engine)
            user = User(id=1)
            session.add_all([user, ])
            session.commit()
            post = Post(id=1, userid=1)
            session.add_all([post, ])
            session.commit()
            self.assertEqual(session.scalars(db.select(Post)).all()[0].id, 1)
            self.assertEqual(session.scalars(db.select(Post)).all()[0].userid, 1)
            with self.assertRaises(sqlalchemy.exc.IntegrityError):
                post = Post(id=2, userid=2)
                session.add_all([post, ])
                session.commit()

    def test_basic_inv(self):
        with Session(self.engine) as session:
            source = """
            Table userb {
                id integer [pk, ref: < postb.userid]
            }

            Table postb {
                id integer [pk]
                userid integer
            }
            """
            parsed = PyDBML(source)
            User = createModel(parsed.tables[0], self.Base)
            Post = createModel(parsed.tables[1], self.Base)
            self.metadata.create_all(self.engine)
            user = User(id=1)
            session.add_all([user, ])
            session.commit()
            post = Post(id=1, userid=1)
            session.add_all([post, ])
            session.commit()
            self.assertEqual(session.scalars(db.select(Post)).all()[0].id, 1)
            self.assertEqual(session.scalars(db.select(Post)).all()[0].userid, 1)
            with self.assertRaises(sqlalchemy.exc.IntegrityError):
                post = Post(id=2, userid=2)
                session.add_all([post, ])
                session.commit()

    def test_multicolumn(self):
        with Session(self.engine) as session:
            source = """
            Table userc {
                id integer
                idd integer
            indexes {
                (id, idd) [pk]
            }
            }

            Table postc {
                id integer [pk]
                userid integer
                useridd integer
            }
            Ref: postc.(userid, useridd) > userc.(id, idd)
            """
            parsed = PyDBML(source)
            User = createModel(parsed.tables[0], self.Base)
            Post = createModel(parsed.tables[1], self.Base)
            self.metadata.create_all(self.engine)
            user = User(id=1, idd=1)
            session.add_all([user, ])
            session.commit()
            post = Post(id=1, userid=1, useridd=1)
            session.add_all([post, ])
            session.commit()
            self.assertEqual(session.scalars(db.select(Post)).all()[0].id, 1)
            self.assertEqual(session.scalars(db.select(Post)).all()[0].userid, 1)
            self.assertEqual(session.scalars(db.select(Post)).all()[0].useridd, 1)
            with self.assertRaises(sqlalchemy.exc.IntegrityError):
                post = Post(id=2, userid=2, useridd=1)
                session.add_all([post, ])
                session.commit()

    def test_relation_basic(self):
        with Session(self.engine) as session:
            source = """
            Table userd {
                id integer [pk, ref: < postd.userid]
            }

            Table postd {
                id integer [pk]
                userid integer
            }
            """
            parsed = PyDBML(source)
            User = createModel(parsed.tables[0], self.Base)
            Post = createModel(parsed.tables[1], self.Base)
            self.metadata.create_all(self.engine)
            user = User(id=1)
            session.add_all([user, ])
            session.commit()
            post = Post(id=1, userid=1)
            session.add_all([post, ])
            session.commit()
            self.assertEqual(session.scalars(db.select(Post)).all()[0].id, 1)
            self.assertEqual(session.scalars(db.select(Post)).all()[0].userid, 1)
            self.assertEqual(session.scalars(db.select(Post)).all()[0].userd.id, 1)
            post = Post(id=2, userid=1)
            session.add_all([post, ])
            session.commit()
            self.assertEqual(len(session.scalars(db.select(User)).all()[0].postds), 2)
