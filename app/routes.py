from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.schema import db, User,Story,Favorite
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_mail import Mail, Message
from datetime import datetime, timedelta,timezone
import random

auth_bp = Blueprint("auth", __name__)
mail = Mail()

@auth_bp.route("/")
def home():
    featured = Story.query.filter_by(is_featured=True).first()
    if current_user.is_authenticated:
        return render_template("home.html", username=current_user.username, featured=featured)
    return render_template("home.html", featured=featured)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email",'').strip()
        password = request.form.get("password", "")

        if not username or not password or not email:
            flash("Username, email and password are required.", "error")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "error")
            return redirect(url_for("auth.register"))
        if User.query.filter_by(email=email).first():
            flash("Email already taken.","error")
            return redirect(url_for("auth.register"))

        user = User(username=username,email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for("auth.home"))

        flash("Invalid username or password.", "error")
        return redirect(url_for("auth.login"))

    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for("auth.home"))



@auth_bp.route("/upload",methods=["GET","POST"])
@login_required
def upload():
    if request.method=="POST":
        title=request.form.get("title","").strip()
        content=request.form.get("content","").strip()
        is_public = "is_public" in request.form
        if not title or not content:
            flash("Title and Content are required","error")
            return redirect(url_for("auth.upload"))
        story = Story(title=title,content=content,author_id=current_user.id,is_public=is_public)
        db.session.add(story)
        db.session.commit()
        flash("Story uploaded sucessfully!","success")
        return redirect(url_for("auth.home"))
    return render_template("upload.html")


@auth_bp.route("/reset_request",methods=["GET","POST"])
def reset_request():
    if request.method=="POST":
        username = request.form.get("username")
        user = User.query.filter_by(username=username).first()
        if not user:
            flash("No user found with that username.","error")
            return redirect(url_for("auth.reset_request"))
        otp=f"{random.randint(100000,999999)}"
        user.otp=otp
        user.otp_expires = datetime.now(timezone.utc) + timedelta(minutes=30)
        db.session.commit()
        print(f"OTP: {otp}, Expires: {user.otp_expires}")
        msg = Message("Password Reset OTP", recipients=[user.email])
        msg.body = f"Your OTP for resetting your password is {otp}. It expires in 10 minutes."
        mail.send(msg)
        flash("OTP sent to your email.", "success")
        return redirect(url_for("auth.reset_password", username=username))
    return render_template("reset_request.html")


@auth_bp.route("/reset_password/<username>",methods=["GET","POST"])
def reset_password(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        flash("Invalid user.","error")
        return redirect(url_for("auth.reset_request"))
    if request.method=="POST":
        otp=request.form.get("otp")
        password=request.form.get("password")
        print(f"Checking OTP: {otp}, Expires: {user.otp_expires}, Now: {datetime.now(timezone.utc).replace(tzinfo=None)}")
        if user.otp!=otp or user.otp_expires<datetime.now(timezone.utc).replace(tzinfo=None):
            flash("Invalid or expired OTP.","error")
            return redirect(url_for("auth.reset_request"))
        user.set_password(password)
        user.otp =None
        user.otp_expires=None
        db.session.commit()
        flash("Password reset successfully.","success")
        return redirect(url_for("auth.login"))
    return render_template("reset_password.html",username=username)

@auth_bp.route('/stories')
def stories():
    all_stories = Story.query.all()
    user_stories = Story.query.filter_by(author_id=current_user.id).all() if current_user.is_authenticated else [] 
    favorite_ids = [f.story_id for f in Favorite.query.filter_by(user_id=current_user.id).all()] if current_user.is_authenticated else []
    return render_template('stories.html', all_stories=all_stories, user_stories=user_stories, username=current_user.username if current_user.is_authenticated else None)

        
@auth_bp.route('/delete_story/<int:story_id>', methods=['POST'])
@login_required
def delete_story(story_id):
    story = Story.query.get_or_404(story_id)
    if story.author_id != current_user.id:
        flash('You can only delete your own stories.', 'error')
        return redirect(url_for('auth.stories'))
    Favorite.query.filter_by(story_id=story_id).delete()
    db.session.delete(story)
    db.session.commit()
    flash('Story deleted successfully.', 'success')
    return redirect(url_for('auth.stories'))


@auth_bp.route('/favorites')
@login_required
def favorites():
    favorites = Favorite.query.filter_by(user_id=current_user.id).all()
    return render_template('favorites.html', favorites=favorites)

@auth_bp.route('/story/<int:story_id>/favorite', methods=['POST'])
@login_required
def favorite_story(story_id):
    story = Story.query.get_or_404(story_id)
    if Favorite.query.filter_by(user_id=current_user.id, story_id=story_id).first():
        flash('You already favorited this story.', 'info')
    else:
        favorite = Favorite(user_id=current_user.id, story_id=story_id)
        db.session.add(favorite)
        db.session.commit()
        flash('Story added to favorites!', 'success')
    return redirect(url_for('auth.stories'))
