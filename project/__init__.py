from flask import Flask
from flask_mysqldb import MySQL
from .db import mysql
from .views import main
from datetime import timedelta

def create_app():
    
    app = Flask(__name__)
    # Secret key
    app.secret_key = 'your_secret_key_here'
    app.permanent_session_lifetime = timedelta(minutes=60)

    # MySQL config
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'whatever'
    app.config['MYSQL_DB'] = 'a2_db'
    app.config['MYSQL_PORT'] = 3307
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

    mysql.init_app(app)

    # Register Blueprints
    app.register_blueprint(main)

    return app
