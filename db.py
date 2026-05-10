import os
from urllib.parse import quote_plus
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    url = os.environ.get('DATABASE_URL')
    if not url:
        user = quote_plus(os.environ.get('POSTGRES_USER', 'user'))
        password = quote_plus(os.environ.get('POSTGRES_PASSWORD', 'password'))
        host = os.environ.get('POSTGRES_HOST', 'db')
        dbname = os.environ.get('POSTGRES_DB', 'taskdb')
        url = f"postgresql://{user}:{password}@{host}:5432/{dbname}"

    app.config['SQLALCHEMY_DATABASE_URI'] = url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()
