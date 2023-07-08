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
            Table user {
                id integer [pk, increment]
            }

            Table post {
                id integer [pk, increment, ref: <> user.id]
            }
            """
            parsed = PyDBML(source)
            User = createModel(parsed.tables[0], self.Base)
            Post = createModel(parsed.tables[1], self.Base)
            self.metadata.create_all(self.engine)
            user = User(id=1)
            session.add_all([user, ])
            session.commit()
            post = Post(id=1)
            session.add_all([post, ])
            session.commit()
            from dbml_to_sqlalchemy.mymodel import Postuser
            postuser = Postuser(post_id=1, user_id=1)
            session.add_all([postuser, ])
            session.commit()
            mypost = session.scalars(db.select(Post)).all()[0]
            self.assertEqual(mypost.postusers[0].user.id, 1)
            self.assertEqual(mypost.users[0].id, 1)
