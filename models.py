from database import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    link = db.Column(db.String(500), nullable=False)
    source = db.Column(db.String(50), nullable=False) # arXiv, Semantic Scholar
    date_saved = db.Column(db.DateTime, default=datetime.utcnow)

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    date_played = db.Column(db.DateTime, default=datetime.utcnow)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admission_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False) # Students name
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(10), default='student')
    
    # Recovery Authentication
    recovery_codes = db.Column(db.String(200), nullable=True) # Comma separated codes

    # Streak System
    quiz_streak = db.Column(db.Integer, default=0)
    last_quiz_date = db.Column(db.Date, nullable=True)

    bookmarks = db.relationship('Bookmark', backref='user', lazy=True, cascade='all, delete-orphan')
    quiz_results = db.relationship('QuizResult', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_recovery_codes(self):
        import string, random
        codes = []
        for _ in range(3):
            # Generate format XXX-XXX
            part1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
            part2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
            codes.append(f"{part1}-{part2}")
        self.recovery_codes = ','.join(codes)
        return codes

    def validate_and_consume_code(self, code):
        if not self.recovery_codes:
            return False
            
        current_codes = self.recovery_codes.split(',')
        clean_input = code.strip().upper()
        
        if clean_input in current_codes:
            current_codes.remove(clean_input)
            self.recovery_codes = ','.join(current_codes)
            return True
            
        return False

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    branch = db.Column(db.String(50), default='BCA', nullable=False) # Default/Hardcoded to BCA
    semester = db.Column(db.String(20), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False) # Notes, PYQs, QuestionBanks
    filepath = db.Column(db.String(200), nullable=False)
    date_uploaded = db.Column(db.DateTime, default=datetime.utcnow)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(50), nullable=False) # Keeping as string for simplicity
    registration_link = db.Column(db.String(200), nullable=False)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False) # 'A', 'B', 'C', or 'D'
