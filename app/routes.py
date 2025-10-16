from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.schema import Like, Progress, db, User,Story,Favorite
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_mail import Mail, Message
from datetime import datetime, timedelta,timezone
import random
import requests
import math
import os
from werkzeug.utils import secure_filename

auth_bp = Blueprint("auth", __name__)
mail = Mail()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif','txt'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth_bp.route('/')
def home():
    most_liked = Story.query.outerjoin(Like).group_by(Story.id).order_by(db.func.count(Like.id).desc(), Story.created_at.desc()).first()
    return render_template('home.html', featured=most_liked, username=current_user.username if current_user.is_authenticated else None)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or len(username) < 3:
            flash('Username must be at least 3 characters.', 'error')
            return render_template('register.html', username=username, email=email)
        if not email or '@' not in email or '.' not in email:
            flash('Valid email is required.', 'error')
            return render_template('register.html', username=username, email=email)
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('register.html', username=username, email=email)
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return render_template('register.html', username=username, email=email)
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html', username=username, email=email)
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

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



@auth_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        file = request.files.get('file')
        visibility = request.form.get('visibility', 'public')

        # Validate title
        if not title:
            flash("Title is required.", "error")
            return render_template('upload.html', username=current_user.username)

        # Handle content: either from textarea or .txt file
        if content and file:
            flash("Please provide content either via text input or file upload, not both.", "error")
            return render_template('upload.html', username=current_user.username)
        elif not content and not file:
            flash("Content is required, either via text input or file upload.", "error")
            return render_template('upload.html', username=current_user.username)
        elif file and allowed_file(file.filename):
            try:
                content = file.read().decode('utf-8')
            except Exception as e:
                flash(f"Error reading file: {str(e)}", "error")
                return render_template('upload.html', username=current_user.username)
        elif content:
            content = content
        else:
            flash("Invalid file format. Only .txt files are allowed.", "error")
            return render_template('upload.html', username=current_user.username)

        # Save story (image_path remains NULL)
        try:
            story = Story(
                title=title,
                content=content,
                author_id=current_user.id,
                is_public=visibility == 'public'
            )
            db.session.add(story)
            db.session.commit()
            flash("Story uploaded successfully!", "success")
            return redirect(url_for('auth.stories'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error uploading story: {str(e)}", "error")
    return render_template('upload.html', username=current_user.username)


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


@auth_bp.route('/reset_password/<username>', methods=['GET', 'POST'])
def reset_password(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        flash('Invalid user.', 'error')
        return redirect(url_for('auth.reset_request'))
    if request.method == 'POST':
        otp = request.form.get('otp')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if user.otp != otp or user.otp_expires < datetime.now(timezone.utc).replace(tzinfo=None):
            flash('Invalid or expired OTP.', 'error')
            return render_template('reset_password.html', username=username)
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html', username=username)
        user.set_password(password)
        user.otp = None
        user.otp_expires = None
        db.session.commit()
        flash('Password reset successfully.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('reset_password.html', username=username)

@auth_bp.route('/story/<int:story_id>', methods=['GET', 'POST'])
def story(story_id):
    story = Story.query.get_or_404(story_id)
    if not story.is_public and (not current_user.is_authenticated or current_user.id != story.author_id):
        flash('You do not have permission to view this story.', 'error')
        return redirect(url_for('auth.stories'))
    favorite_ids = [f.story_id for f in Favorite.query.filter_by(user_id=current_user.id).all()] if current_user.is_authenticated else []
    position = 0
    if current_user.is_authenticated:
        progress = Progress.query.filter_by(user_id=current_user.id, story_id=story_id).first()
        position = progress.position if progress else 0
        if request.method == 'POST':
            position = round(float(request.form.get('position', 0)))
            print(f"POST received: story_id={story_id}, user_id={current_user.id}, position={position}")
            if not progress:
                progress = Progress(user_id=current_user.id, story_id=story_id, position=position, book_id=None)
                db.session.add(progress)
            else:
                progress.position = position
            db.session.commit()
            print(f"Progress saved: {progress.id}, position={progress.position}")
            flash("Reading progress saved!", "success")
    return render_template(
        'story.html',
        story=story,
        favorite_ids=favorite_ids,
        position=position,
        username=current_user.username if current_user.is_authenticated else None
    )


@auth_bp.route('/stories', methods=['GET'])
def stories():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')
    query = Story.query.filter_by(is_public=True)
    if search_query:
        query = query.filter(Story.title.ilike(f'%{search_query}%'))
    stories = query.order_by(Story.created_at.desc()).paginate(page=page, per_page=10)
    liked_ids = [l.story_id for l in Like.query.filter_by(user_id=current_user.id).all()] if current_user.is_authenticated else []
    return render_template('stories.html', stories=stories.items, page=page, search_query=search_query,
                          prev_page=stories.has_prev, next_page=stories.has_next, liked_ids=liked_ids,
                          username=current_user.username if current_user.is_authenticated else None)

        
@auth_bp.route('/delete/<int:story_id>', methods=['POST'])
@login_required
def delete_story(story_id):
    story = Story.query.get_or_404(story_id)
    if current_user.id != story.author_id:
        flash("You are not authorized to delete this story.", "error")
        return redirect(url_for('auth.my_stories'))
    db.session.delete(story)
    db.session.commit()
    flash("Story deleted successfully!", "success")
    return redirect(url_for('auth.my_stories'))


@auth_bp.route('/favorites', methods=['GET'])
@login_required
def favorites():
    favorites = Favorite.query.filter_by(user_id=current_user.id).all()
    book_favorites = []
    story_favorites = []
    for favorite in favorites:
        if favorite.book_id:
            try:
                response = requests.get(f"https://gutendex.com/books/{favorite.book_id}")
                response.raise_for_status()
                book_data = response.json()
                formats = book_data.get('formats', {})
                book_favorites.append({
                    'id': favorite.book_id,
                    'title': book_data.get('title', 'Unknown Title'),
                    'authors': ', '.join(author['name'] for author in book_data.get('authors', [])),
                    'image_url': formats.get('image/jpeg', '/static/images/placeholder.jpg')
                })
            except requests.RequestException:
                book_favorites.append({
                    'id': favorite.book_id,
                    'title': 'Error fetching book',
                    'authors': '',
                    'image_url': '/static/images/placeholder.png'
                })
        elif favorite.story_id:
            story = Story.query.get(favorite.story_id)
            if story:
                story_favorites.append({
                    'id': story.id,
                    'title': story.title,
                    'author': story.author.username,
                    'image_url': '/static/images/placeholder.png' 
                })
    return render_template('favorites.html', story_favorites=story_favorites, book_favorites=book_favorites, username=current_user.username)

@auth_bp.route('/story/<int:story_id>/favorite', methods=['POST'])
@login_required
def favorite_story(story_id):
    story = Story.query.get_or_404(story_id)
    favorite = Favorite.query.filter_by(user_id=current_user.id, story_id=story_id).first()
    if favorite:
        db.session.delete(favorite)
        flash('Story removed from favorites.', 'success')
    else:
        favorite = Favorite(user_id=current_user.id, story_id=story_id, book_id=None)
        db.session.add(favorite)
        flash('Story added to favorites!', 'success')
    db.session.commit()
    return redirect(request.referrer or url_for('auth.stories'))

@auth_bp.route('/favorite_book/<int:book_id>', methods=['POST'])
def favorite_book(book_id):
    if not current_user.is_authenticated:
        flash('Please log in to favorite a book.', 'error')
        return redirect(url_for('auth.login'))
    favorite = Favorite.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    if favorite:
        db.session.delete(favorite)
        flash('Book removed from favorites.', 'success')
    else:
        favorite = Favorite(user_id=current_user.id, book_id=book_id, story_id=None)
        db.session.add(favorite)
        flash('Book added to favorites!', 'success')
    db.session.commit()
    return redirect(request.referrer or url_for('auth.books'))

@auth_bp.route('/books', methods=['GET'])
def books():
    try:
        page = int(request.args.get('page', 1))
        search_query = request.args.get('search', '')
        params = {'page': page}
        if search_query:
            params['search'] = search_query
        response = requests.get("https://gutendex.com/books", params=params)
        response.raise_for_status()
        data = response.json()
        books = data.get('results', [])
        total_books = data.get('count', 0)
        total_pages = math.ceil(total_books / 32)  # Gutendex returns 32 books per page
        for book in books:
            formats = book.get('formats', {})
            book['image_url'] = formats.get('image/jpeg', '/static/images/placeholder.png')
            book['is_favorited'] = False
        if current_user.is_authenticated:
            favorite_book_ids = {f.book_id for f in Favorite.query.filter_by(user_id=current_user.id).all() if f.book_id}
            for book in books:
                book['is_favorited'] = book['id'] in favorite_book_ids
        prev_page = data.get('previous')
        next_page = data.get('next')
        return render_template('books.html', books=books, page=page, search_query=search_query,
                              prev_page=prev_page, next_page=next_page, total_pages=total_pages,
                              username=current_user.username if current_user.is_authenticated else None)
    except requests.RequestException as e:
        flash(f"Failed to fetch books: {str(e)}", "error")
        return render_template('books.html', books=[], page=1, search_query='', prev_page=None, next_page=None, total_pages=0, username=None)


@auth_bp.route('/book/<int:book_id>', methods=['GET', 'POST'])
def book(book_id):
    try:
        response = requests.get(f"https://gutendex.com/books/{book_id}")
        response.raise_for_status()
        book_data = response.json()
        formats = book_data.get("formats", {})
        text_url = (
            formats.get("text/plain") or
            formats.get("text/plain; charset=utf-8") or
            formats.get("text/plain; charset=us-ascii") or
            formats.get("text/plain; charset=iso-8859-1")
        )
        image_url = formats.get('image/jpeg', '/static/images/placeholder.png')
        if not text_url:
            flash(f"No plain text format available for {book_data.get('title', 'this book')}.", "error")
            return redirect(url_for("auth.books"))
        text_response = requests.get(text_url)
        text_response.raise_for_status()
        book_content = text_response.text
        position = 0
        is_favorited = False
        if current_user.is_authenticated:
            progress = Progress.query.filter_by(user_id=current_user.id, book_id=book_id).first()
            position = progress.position if progress else 0
            favorite = Favorite.query.filter_by(user_id=current_user.id, book_id=book_id).first()
            is_favorited = bool(favorite)
            if request.method == 'POST':
                try:
                    position = round(float(request.form.get('position', 0)))
                    print(f"POST received: book_id={book_id}, user_id={current_user.id}, position={position}")
                    if not progress:
                        progress = Progress(user_id=current_user.id, book_id=book_id, position=position, story_id=None)
                        db.session.add(progress)
                    else:
                        progress.position = position
                    db.session.commit()
                    print(f"Progress saved: progress_id={progress.id if progress else 'None'}, position={position}")
                    flash("Reading progress saved!", "success")
                except ValueError as e:
                    print(f"Invalid position value: {e}")
                    flash("Error saving progress: Invalid position.", "error")
                except Exception as e:
                    print(f"Error saving progress: {e}")
                    flash("Error saving progress.", "error")
        return render_template(
            "book.html",
            book=book_data,
            content=book_content,
            image_url=image_url,
            position=position,
            is_favorited=is_favorited,
            username=current_user.username if current_user.is_authenticated else None
        )
    except requests.RequestException as e:
        print(f"Error in book route: {str(e)}")
        flash(f"Failed to fetch book: {str(e)}", "error")
        return redirect(url_for("auth.books"))


@auth_bp.route('/like/<int:story_id>', methods=['POST'])
@login_required
def like_story(story_id):
    story = Story.query.get_or_404(story_id)
    like = Like.query.filter_by(user_id=current_user.id, story_id=story_id).first()
    if like:
        db.session.delete(like)
        flash('Story unliked.', 'success')
    else:
        like = Like(user_id=current_user.id, story_id=story_id)
        db.session.add(like)
        flash('Story liked!', 'success')
    db.session.commit()
    return redirect(request.referrer or url_for('auth.stories'))

@auth_bp.route('/my_stories', methods=['GET'])
@login_required
def my_stories():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')
    query = Story.query.filter_by(author_id=current_user.id)
    if search_query:
        query = query.filter(Story.title.ilike(f'%{search_query}%'))
    stories = query.paginate(page=page, per_page=10)
    liked_ids = [l.story_id for l in Like.query.filter_by(user_id=current_user.id).all()]
    favorite_ids = [f.story_id for f in Favorite.query.filter_by(user_id=current_user.id).all() if f.story_id]
    return render_template('my_stories.html', stories=stories.items, page=page, search_query=search_query,
                          prev_page=stories.has_prev, next_page=stories.has_next, liked_ids=liked_ids,
                          favorite_ids=favorite_ids, username=current_user.username)