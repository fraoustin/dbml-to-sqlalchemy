# dbml-to-sqlalchemy

generate Model Class SqlAlchemy from database model dbml


## Installation


::

    pip install dbml-to-sqlalchemy
        
Or

::

    git clone https://github.com/fraoustin/dbml-to-sqlalchemy.git
    cd dbml-to-sqlalchemy
    python setup.py install

You can load test by

::

    flake8 --ignore E501,E226,E128,F401
    python -m unittest discover -s tests


## Usage

for sqlalchemy only 

::

    import os
    from re import sub
    import sqlalchemy as db
    from pydbml import PyDBML

    from dbml_to_sqlalchemy import createModel


    database_file = "sqlite://"
    engine = db.create_engine(database_file, echo=True)
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
    id integer [primary key]
    username varchar
    role varchar
    created_at timestamp
    }
    """

    parsed = PyDBML(source)

    User = createModel(parsed.tables[0], Base)
    print(User.__name__)

    metadata.create_all(engine)


for flask-sqlalchemy

::

    import os
    import logging
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    from pydbml import PyDBML
    from dbml_to_sqlalchemy import createModel, mymodel

    app = Flask(__name__)

    # db SQLAlchemy
    database_file = "sqlite://"
    app.config["SQLALCHEMY_DATABASE_URI"] = database_file
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db = SQLAlchemy()

    source = """
    Table user {
    id integer [primary key]
    username varchar
    role varchar
    created_at timestamp
    }
    """

    parsed = PyDBML(source)
    createModel(parsed.tables[0], db.Model)


    def model_to_dict(obj):
        return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


    @app.route('/me')
    def mepath():
        return model_to_dict(mymodel.User.query.filter_by(id=1).first()), 200


    if __name__ == "__main__":
        db.init_app(app)
        with app.app_context():
            db.create_all()
            me = mymodel.User(id=1, username='me')
            db.session.add_all([me, ])
            db.session.commit()
        app.logger.setLevel(logging.DEBUG)
        app.run(host='0.0.0.0', port=5000, debug=True)

## TODO