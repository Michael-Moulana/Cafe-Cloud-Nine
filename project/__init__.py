from flask import Flask
from flask_mysqldb import MySQL

mysql = MySQL()

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your_secret_key_here'

    # MySQL configuration for Flask-MySQLdb
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'sqlhriqut'
    app.config['MYSQL_DB'] = 'a2_db'
    app.config['MYSQL_PORT'] = 3306
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor'  # Flask-MySQLdb expects a string

    mysql.init_app(app)

    with app.app_context():
        from .views import main
        app.register_blueprint(main)

    return app