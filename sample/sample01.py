import os
from re import sub
import sqlalchemy as db
from sqlalchemy.orm import Session
from pydbml import PyDBML

from dbml_to_sqlalchemy import createModel
from dbml_to_sqlalchemy import mymodel

database_file = "sqlite://"
engine = db.create_engine(database_file, echo=False)
conn = engine.connect()
metadata = db.MetaData()


try:
    from sqlalchemy.orm import DeclarativeBase

    class Base(DeclarativeBase):
        metadata = metadata
except Exception:
    # for sqlalchemy 1.4
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()

source = """
Table user {
    id integer [pk, increment, note:'key of user']
    name string [default: 'me', note:'only name']
}

Table post {
    id integer [pk, increment]
    user_id integer [ref: > user.id]
}
"""

parsed = PyDBML(source)


User = createModel(parsed.tables[0], Base)
Post = createModel(parsed.tables[1], Base)

print(User.__doc__)
print(Post.__doc__)

metadata.create_all(engine)

with Session(engine) as session:
    user = User(id=1)
    session.add_all([user, ])
    session.commit()
    post = Post(id=1, user_id=1)
    session.add_all([post, ])
    session.commit()
    mypost = session.scalars(db.select(Post)).all()[0]
    print(mypost.user.name)
