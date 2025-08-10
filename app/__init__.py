from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_moment import Moment # Import Flask-Moment
from config import Config

db = SQLAlchemy()
login = LoginManager()
migrate = Migrate()
moment = Moment() # Initialize Flask-Moment

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login.init_app(app)
    migrate.init_app(app, db)
    moment.init_app(app) # Register Flask-Moment with the app

    login.login_view = 'auth.login'
    login.login_message_category = 'info'

    # Import and register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.marketer import bp as marketer_bp
    app.register_blueprint(marketer_bp, url_prefix='/marketer')

    from app.customer import bp as customer_bp
    app.register_blueprint(customer_bp)

    # Create default admin
    with app.app_context():
        from app.models import User
        # Create tables if they don't exist before creating admin
        db.create_all()
        User.create_default_admin(
            username=app.config['ADMIN_USERNAME'],
            email=app.config['ADMIN_EMAIL'],
            password=app.config['ADMIN_PASSWORD']
        )

    return app

