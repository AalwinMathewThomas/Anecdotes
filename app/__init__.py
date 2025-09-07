from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from app.schema import db, User  
import os

login_manager = LoginManager()
mail = Mail()

def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.join(base_dir, "..", "templates")
    instance_dir = os.path.abspath(os.path.join(base_dir, "..")) 

    app = Flask(__name__, template_folder=template_dir, instance_path=instance_dir)

    app.config['SECRET_KEY'] = 'df950b388400d919d9b673c5b42605bd923fd3e0703dae13d0dbbef06c2522e8'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///anecdotes.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAIL_SERVER']='smtp-relay.brevo.com'
    app.config['MAIL_PORT']='587'
    app.config['MAIL_USE_TLS']=True
    app.config['MAIL_USERNAME']='9677ac001@smtp-brevo.com'
    app.config['MAIL_PASSWORD']='gaTtCXp64mNBQLq1'
    app.config['MAIL_DEFAULT_SENDER']='aalwin.mathew.thomas@gmail.com'



    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  
    mail.init_app(app)


    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))


    from app.routes import auth_bp
    app.register_blueprint(auth_bp)


    with app.app_context():
        db.create_all()

    return app
