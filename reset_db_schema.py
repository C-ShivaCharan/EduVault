from app import create_app
from database import db
from models import User

app = create_app()

with app.app_context():
    print("Dropping all tables...")
    db.drop_all()
    print("Recreating tables with new schema...")
    db.create_all()
    
    print("Creating default admin...")
    # Admin
    if not User.query.filter_by(admission_number='admin').first():
        admin = User(admission_number='admin', name='Admin User', role='admin')
        admin.set_password('password123')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created (admin / password123)")
    
    print("Database reset complete!")
