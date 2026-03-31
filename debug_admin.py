from app import create_app
from models import User

app = create_app()

with app.app_context():
    # specifically check the user 'admin'
    admin = User.query.filter_by(admission_number='admin').first()
    if admin:
        print(f"User: {admin.admission_number}")
        print(f"Name: {admin.name}")
        print(f"Role: {admin.role}")
        print(f"ID: {admin.id}")
    else:
        print("User 'admin' not found.")
