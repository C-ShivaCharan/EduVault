from flask import Flask
from database import db
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev_secret_key' # Change for production
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
       


    # Register blueprints
    from routes import main_bp
    app.register_blueprint(main_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    # Host='0.0.0.0' allows access from external connections (tunnels/LAN)
    app.run(debug=True, host='0.0.0.0', port=5000)
