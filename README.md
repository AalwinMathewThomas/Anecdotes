Anecdotes

Welcome to Anecdotes, a full-stack web application built with Flask where users can share personal stories, favorite content, and explore classic books from the Gutenberg API with progress tracking.
Overview
Purpose: A platform for users to register, upload stories, track reading progress, and browse classic literature.
Features: User authentication (login/logout, OTP password reset via Brevo SMTP), favorites, private story viewing, and responsive UI.
Tech Stack: Flask, SQLAlchemy, PostgreSQL, Bootstrap 5, Jinja2, Flask-Login, Flask-Mail, Render, Git/GitHub.

Live Demo: https://anecdotes-0vzl.onrender.com

1)Clone the repository:

git clone https://github.com/AalwinMathewThomas/Anecdotes.git
cd Anecdotes


2)Install dependencies:

pip install -r requirements.txt



3)Set up environment variables in a .env file:

DATABASE_URL=your_local_sqlite_db
SECRET_KEY=your_secure_key
MAIL_SERVER=smtp-relay.brevo.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_brevo_username
MAIL_PASSWORD=your_brevo_password
MAIL_DEFAULT_SENDER=your_email

Register, log in, and start sharing stories or exploring books.

Deployment
Deployed on Render with Gunicorn and PostgreSQL.



Start command: gunicorn wsgi_app:app.

Environment variables managed via Render dashboard.
