from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
db = SQLAlchemy()
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)


    stories = db.relationship('Story', backref='author', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)
    progress = db.relationship('Progress', backref='user', lazy=True)


    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

class Story(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(200),nullable=False)
    content = db.Column(db.Text,nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_featured = db.Column(db.Boolean,default=False)
    is_gutenberg = db.Column(db.Boolean,default=False)

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)

class Progress(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    position = db.Column(db.Integer, default=0)




