from flask import Flask
from database import db
import os
from dotenv import load_dotenv

# Force load_dotenv to look in the exact directory of app.py
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key') # Change for production
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eduvault.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
    
    # Auth Config
    from flask_login import LoginManager
    login_manager = LoginManager()
    login_manager.login_view = 'main.login'
    login_manager.init_app(app)

    db.init_app(app)
    
    from models import User, Material, Event, Question, QuizResult

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        # Import models and create tables
        db.create_all()
        
        # Check if DB is initialized 
        admin_user = User.query.filter_by(role='admin').first()
        if not admin_user:
            admin = User(
                admission_number='admin',
                name='Admin User',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Database seeded: Default admin user created.")


    # Register blueprints
    from routes import main_bp
    app.register_blueprint(main_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    # Host='0.0.0.0' allows access from external connections (tunnels/LAN)
    app.run(debug=False, host='0.0.0.0', port=5000)
