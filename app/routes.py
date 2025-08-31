from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.schema import db, User,Story

auth_bp = Blueprint("auth", __name__)

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
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.", "error")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "error")
            return redirect(url_for("auth.register"))

        user = User(username=username)
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
        if not title or content:
            flash("Title and Content are required","error")
            return redirect(url_for("auth.upload"))
        story = Story(title=title,content=content,author_id=current_user.id)
        db.session.add(story)
        db.session.commit()
        flash("Story uploaded sucessfully!","sucess")
        return redirect(url_for("auth.home"))
    return render_template("upload.html")





