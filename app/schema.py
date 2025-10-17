from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    otp = db.Column(db.String(6))
    otp_expires = db.Column(db.DateTime)
    stories = db.relationship('Story', backref='author', lazy=True)
    favorites = db.relationship('Favorite', backref='favorited_user', lazy=True)
    progress = db.relationship('Progress', backref='progress_user', lazy=True)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

class Story(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_featured = db.Column(db.Boolean, default=False)
    is_gutenberg = db.Column(db.Boolean, default=False)
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow) 
    likes = db.relationship('Like', backref='liked_story', lazy=True, cascade='all, delete-orphan')
    image_path = db.Column(db.String(200), nullable=True)

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id', ondelete='CASCADE'), nullable=True)
    book_id = db.Column(db.Integer, nullable=True)
    user = db.relationship('User', backref='user_favorites', lazy=True)
    story = db.relationship('Story', backref='story_favorites', lazy=True)

class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id', ondelete='CASCADE'), nullable=True)
    book_id = db.Column(db.Integer, nullable=True)
    position = db.Column(db.Integer, default=0)
    user = db.relationship('User', backref='progress_user', lazy=True)
    story = db.relationship('Story', backref='story_progress', lazy=True)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id', ondelete='CASCADE'), nullable=False)
    user = db.relationship('User', backref='likes', lazy=True)
    story = db.relationship('Story', lazy=True)