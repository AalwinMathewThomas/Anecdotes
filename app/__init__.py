from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    

    app.config['SECRET_KEY'] = '490f5b3a23c26ce4d4457c046abc58d2'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///anecdotes.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)


    from app.schema import User, Story, Favorite, Progress

    with app.app_context():
        db.create_all()

    @app.route('/')
    def home():
        return 'Welcome to Anecdotes!'

    return app
