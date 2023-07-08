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
