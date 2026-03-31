from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_from_directory, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import User, Material, Event, Question, QuizResult, db
import os
from werkzeug.utils import secure_filename

main_bp = Blueprint('main', __name__)

# --- Routes ---

@main_bp.route('/')
def index():
    if current_user.is_authenticated and current_user.role == 'admin':
        return redirect(url_for('main.admin_dashboard'))

    today_date = None
    
    # Dashboard Data
    materials_count = Material.query.count()
    upcoming_event = Event.query.order_by(Event.date.asc()).first() # Simple fetch
    
    high_score = 0
    recent_quiz = None
    
    if current_user.is_authenticated:
        recent_quiz = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.date_played.desc()).first()
        best_quiz = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.score.desc()).first()
        if best_quiz:
            high_score = best_quiz.score

    return render_template('index.html', 
                           recent_quiz=recent_quiz, 
                           materials_count=materials_count, 
                           upcoming_event=upcoming_event,
                           high_score=high_score)

@main_bp.route('/sw.js')
def service_worker():
    return send_from_directory(os.path.join(current_app.root_path, 'static'), 'sw.js', mimetype='application/javascript')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        admission_number = request.form.get('admission_number')
        password = request.form.get('password')
        
        if User.query.filter_by(admission_number=admission_number).first():
            flash('Admission Number already registered')
        else:
            security_question = request.form.get('security_question')
            security_answer = request.form.get('security_answer')
            
            user = User(admission_number=admission_number, name=name, role='student')
            user.set_password(password)
            
            if security_question and security_answer:
                user.security_question = security_question
                user.set_security_answer(security_answer)
                
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('main.login'))
            
    return render_template('register.html')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        admission_number = request.form.get('admission_number')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(admission_number=admission_number).first()
        
        # Check password AND name if provided (Case insensitive check for name)
        if user and user.check_password(password):
            if name and user.name and name.strip().lower() != user.name.strip().lower():
                flash('Name does not match Admission Number.')
            else:
                login_user(user, remember=remember)
                return redirect(url_for('main.index'))
        else:
            flash('Invalid admission number or password')
            
    return render_template('login.html')

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        admission_number = request.form.get('admission_number')
        user = User.query.filter_by(admission_number=admission_number).first()
        
        if user:
            if user.security_question and user.security_answer_hash:
                # User has security setup, proceed to Step 2
                return render_template('reset_security.html', question=user.security_question, user_id=user.id)
            else:
                flash('This account does not have a security question set up. Contact Admin.')
        else:
            flash('Admission Number not found.')
            
    return render_template('forgot_password.html')

@main_bp.route('/reset_security/<int:user_id>', methods=['POST'])
def reset_security(user_id):
    user = User.query.get_or_404(user_id)
    
    answer = request.form.get('security_answer')
    new_password = request.form.get('new_password')
    
    if user.check_security_answer(answer):
        user.set_password(new_password)
        db.session.commit()
        flash('Password reset successful! Please login.')
        return redirect(url_for('main.login'))
    else:
        flash('Incorrect Security Answer.')
        return render_template('reset_security.html', question=user.security_question, user_id=user.id)


# --- Admin Routes ---
@main_bp.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Unauthorized Access.')
        return redirect(url_for('main.index'))
        
    # Stats
    total_users = User.query.count()
    total_materials = Material.query.count()
    total_events = Event.query.count()
    
    # Recent users
    users = User.query.order_by(User.id.desc()).all()
    
    return render_template('admin_dashboard.html', 
                            total_users=total_users, 
                            total_materials=total_materials,
                            total_events=total_events,
                            users=users)

@main_bp.route('/admin/user/delete/<int:id>', methods=['POST'])
@login_required
def delete_user(id):
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))
        
    user = User.query.get_or_404(id)
    if user.role == 'admin':
        flash('Cannot delete admin account.')
    else:
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.name} deleted.')
        
    return redirect(url_for('main.admin_dashboard'))

@main_bp.route('/admin/user/reset/<int:id>', methods=['POST'])
@login_required
def admin_reset_password(id):
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))
        
    user = User.query.get_or_404(id)
    new_password = 'password123' # Default reset password
    user.set_password(new_password)
    db.session.commit()
    flash(f'Password for {user.name} reset to: {new_password}')
    
    return redirect(url_for('main.admin_dashboard'))



# --- Materials ---
@main_bp.route('/materials')
@login_required
def materials():
    return render_template('materials.html')

@main_bp.route('/materials/<semester>', methods=['GET'])
@login_required
def semester_view(semester):
    # Validate semester
    valid_sems = ['Sem1', 'Sem2', 'Sem3', 'Sem4', 'Sem5', 'Sem6']
    if semester not in valid_sems:
        return redirect(url_for('main.materials'))
        
    # Fetch BCA materials for this semester
    all_materials = Material.query.filter_by(branch='BCA', semester=semester).all()
    
    syllabus_files = []
    subjects = {}
    
    for m in all_materials:
        if m.type == 'Syllabus':
            syllabus_files.append(m)
            continue
            
        if m.subject not in subjects:
            subjects[m.subject] = {'Textbooks': [], 'Notes': [], 'ImportantQuestions': [], 'PYQs': [], 'QuestionBanks': []}
        
        # Ensure list exists for type (formatting safety)
        if m.type not in subjects[m.subject]:
            subjects[m.subject][m.type] = []
            
        subjects[m.subject][m.type].append(m)
        
    return render_template('semester_view.html', semester=semester, subjects=subjects, syllabus_files=syllabus_files)

@main_bp.route('/materials/upload', methods=['POST'])
@login_required
def upload_material():
    if current_user.role != 'admin':
        flash('Unauthorized')
        return redirect(url_for('main.materials'))

    file = request.files.get('file')
    title = request.form.get('title')
    semester = request.form.get('semester')
    m_type = request.form.get('type')
    
    # Subject is optional for Syllabus
    subject = request.form.get('subject')
    if m_type == 'Syllabus':
        subject = 'General'
    
    if file and title and semester and subject and m_type:
        filename = secure_filename(file.filename)
        from flask import current_app
        base_path = current_app.config['UPLOAD_FOLDER']
        save_dir = os.path.join(base_path, 'BCA', semester, m_type)
        os.makedirs(save_dir, exist_ok=True)
        
        file_path = os.path.join(save_dir, filename)
        rel_path = os.path.join('uploads', 'BCA', semester, m_type, filename).replace('\\', '/')
        
        file.save(file_path)
        
        new_material = Material(
            title=title,
            branch='BCA',
            semester=semester,
            subject=subject,
            type=m_type,
            filepath=rel_path
        )
        db.session.add(new_material)
        db.session.commit()
        flash('Material uploaded successfully!')
        return redirect(url_for('main.semester_view', semester=semester))
    else:
        flash('All fields required')
        return redirect(url_for('main.materials'))

@main_bp.route('/materials/delete/<int:id>', methods=['POST'])
@login_required
def delete_material(id):
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))
        
    material = Material.query.get_or_404(id)
    sem = material.semester # Store for redirect
    # Optional: Delete physical file
    # try:
    #     os.remove(os.path.join('static', material.filepath))
    # except:
    #     pass
    db.session.delete(material)
    db.session.commit()
    flash('Material deleted')
    return redirect(url_for('main.semester_view', semester=sem))

# --- Bookmarks ---
@main_bp.route('/bookmarks')
@login_required
def bookmarks():
    from models import Bookmark
    bookmarks_list = Bookmark.query.filter_by(user_id=current_user.id).order_by(Bookmark.date_saved.desc()).all()
    return render_template('bookmarks.html', bookmarks=bookmarks_list)

@main_bp.route('/bookmarks/add', methods=['POST'])
@login_required
def add_bookmark():
    from models import Bookmark
    title = request.form.get('title')
    link = request.form.get('link')
    source = request.form.get('source')
    
    if title and link and source:
        # Check duplicate
        exists = Bookmark.query.filter_by(user_id=current_user.id, link=link).first()
        if not exists:
            bm = Bookmark(user_id=current_user.id, title=title, link=link, source=source)
            db.session.add(bm)
            db.session.commit()
            flash('Paper added to bookmarks!')
        else:
            flash('Paper already bookmarked.')
    
    # Redirect back to whence they came, or default to research
    return redirect(request.referrer or url_for('main.research'))

@main_bp.route('/bookmarks/remove/<int:id>', methods=['POST'])
@login_required
def remove_bookmark(id):
    from models import Bookmark
    bm = Bookmark.query.get_or_404(id)
    if bm.user_id == current_user.id:
        db.session.delete(bm)
        db.session.commit()
        flash('Bookmark removed')
    return redirect(url_for('main.bookmarks'))

# --- APIs (Research & Books) ---
@main_bp.route('/research')
@login_required
def research():
    query = request.args.get('query')
    results = []
    
    if query:
        import requests
        import xml.etree.ElementTree as ET

        # 1. arXiv API
        try:
            url = f'http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results=5'
            response = requests.get(url)
            root = ET.fromstring(response.content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            for entry in root.findall('atom:entry', ns):
                title = entry.find('atom:title', ns).text.strip()
                summary_node = entry.find('atom:summary', ns)
                summary = summary_node.text.strip() if summary_node is not None else "No abstract"
                link = entry.find('atom:id', ns).text.strip()
                authors = [author.find('atom:name', ns).text for author in entry.findall('atom:author', ns)]
                
                results.append({
                    'title': title,
                    'abstract': summary,
                    'link': link,
                    'authors': ', '.join(authors),
                    'source': 'arXiv'
                })
        except Exception as e:
            print(f"arXiv Error: {e}")

        # 2. Semantic Scholar API
        try:
            url = f'https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit=5&fields=title,abstract,authors,url,openAccessPdf'
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                for paper in data.get('data', []):
                    authors = [a['name'] for a in paper.get('authors', [])]
                    link = paper.get('url') or (paper.get('openAccessPdf') or {}).get('url')
                    
                    if link: # Only add if link exists
                        results.append({
                            'title': paper.get('title'),
                            'abstract': paper.get('abstract') or "No abstract available.",
                            'link': link,
                            'authors': ', '.join(authors),
                            'source': 'Semantic Scholar'
                        })
        except Exception as e:
            print(f"Semantic Scholar Error: {e}")

        # 3. Crossref API
        try:
            url = f'https://api.crossref.org/works?query={query}&rows=5'
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                for item in data['message']['items']:
                    title = item.get('title', ['No Title'])[0]
                    # Abstract is rare in Crossref public result list, usually just metadata
                    link = item.get('URL')
                    authors_list = item.get('author', [])
                    authors = [f"{a.get('given','')} {a.get('family','')}" for a in authors_list]
                    
                    results.append({
                        'title': title,
                        'abstract': "Click link to view full details.",
                        'link': link,
                        'authors': ', '.join(authors),
                        'source': 'Crossref'
                    })
        except Exception as e:
            print(f"Crossref Error: {e}")
            
    return render_template('research.html', results=results, query=query)

@main_bp.route('/ebooks')
@login_required
def ebooks():
    query = request.args.get('query')
    results = []
    
    if query:
        import requests
        
        # 1. OpenLibrary API (Prioritizing Free Full Text)
        try:
            # Add has_fulltext=true to specifically find readable books
            url = f'https://openlibrary.org/search.json?q={query}&has_fulltext=true&limit=10'
            response = requests.get(url, timeout=5)
            data = response.json()
            
            for doc in data.get('docs', []):
                cover_id = doc.get('cover_i')
                # Construct direct reading link using Internet Archive ID (ia) or Open Library Key
                # If 'ia' collection id exists, we can link directly to archive.org stream
                ia_id = doc.get('ia', [None])[0]
                
                if ia_id:
                    read_link = f"https://archive.org/details/{ia_id}/mode/2up"
                    download_link = f"https://archive.org/download/{ia_id}/{ia_id}.pdf"
                else:
                    # Fallback to Open Library reader
                    read_link = f"https://openlibrary.org{doc.get('key')}"
                    download_link = None # Cannot guarantee PDF
                
                results.append({
                    'title': doc.get('title'),
                    'author': doc.get('author_name', ['Unknown'])[0],
                    'cover': f'https://covers.openlibrary.org/b/id/{cover_id}-M.jpg' if cover_id else 'https://via.placeholder.com/128x192?text=No+Cover',
                    'link': read_link,
                    'pdf_link': download_link,
                    'is_readable': True,
                    'source': 'OpenLibrary / Archive.org'
                })
        except Exception as e:
            print(f"OpenLibrary Error: {e}")

        # 2. Google Books API (Backup - often previews only)
        try:
            url = f'https://www.googleapis.com/books/v1/volumes?q={query}&filter=free-ebooks&maxResults=5'
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                for item in data.get('items', []):
                    info = item.get('volumeInfo', {})
                    authors = info.get('authors', ['Unknown'])
                    image_links = info.get('imageLinks', {})
                    access_info = item.get('accessInfo', {})
                    
                    pdf_link = access_info.get('pdf', {}).get('downloadLink')
                    
                    results.append({
                        'title': info.get('title'),
                        'author': authors[0],
                        'cover': image_links.get('thumbnail') or 'https://via.placeholder.com/128x192?text=No+Cover',
                        'link': info.get('previewLink') or info.get('infoLink'),
                        'pdf_link': pdf_link,
                        'is_readable': access_info.get('publicDomain', False), # True if public domain
                        'source': 'Google Books (Free)'
                    })
        except Exception as e:
            print(f"Google Books Error: {e}")
            
    return render_template('ebooks.html', results=results, query=query)

@main_bp.route('/journals')
@login_required
def journals():
    query = request.args.get('query')
    results = []
    
    if query:
        import requests
        try:
            # DOAJ API
            url = f'https://doaj.org/api/search/articles/{query}?pageSize=10'
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                for item in data.get('results', []):
                    bibjson = item.get('bibjson', {})
                    journal = bibjson.get('journal', {})
                    
                    results.append({
                        'title': bibjson.get('title'),
                        'journal': journal.get('title'),
                        'abstract': bibjson.get('abstract') or "No abstract.",
                        'link': (bibjson.get('link') or [{}])[0].get('url'),
                        'source': 'DOAJ'
                    })
        except Exception as e:
            print(f"DOAJ Error: {e}")
            
    return render_template('journals.html', results=results, query=query)

# --- Events ---
@main_bp.route('/events', methods=['GET', 'POST'])
@login_required
def events():
    # Admin Add Event Logic
    if request.method == 'POST':
        if not current_user.is_authenticated or current_user.role != 'admin':
             flash('Unauthorized')
             return redirect(url_for('main.events'))
             
        name = request.form.get('name')
        description = request.form.get('description')
        date = request.form.get('date')
        link = request.form.get('link')
        
        if name and description and date and link:
            new_event = Event(name=name, description=description, date=date, registration_link=link)
            db.session.add(new_event)
            db.session.commit()
            flash('Event added successfully')
            return redirect(url_for('main.events'))
        else:
            flash('All fields are required')

    # Fetch API Events
    import requests
    from datetime import datetime, timedelta
    import re
    
    online_events = []
    offline_events = []
    
    current_year = datetime.now().year
    current_month = datetime.now().strftime('%m')
    month_name = datetime.now().strftime('%B')
    
    # 1. Try Hackalist API
    try:
        url = f"https://www.hackalist.org/api/1.0/{current_year}/{current_month}.json"
        resp = requests.get(url, timeout=2) 
        
        if resp.status_code == 200:
            data = resp.json()
            api_data = data.get(month_name, [])
            for e in api_data:
                city = e.get('city', '').lower()
                if 'online' in city or 'web' in city or 'remote' in city:
                    online_events.append(e)
    except Exception as e:
        print(f"Hackalist API Error: {e}")

    # 2. Scrape MLH (Major League Hacking) if Hackalist failed or empty
    if not online_events:
        try:
            # Try current season (Academic year usually)
            season = current_year if datetime.now().month < 7 else current_year + 1
            mlh_url = f"https://mlh.io/seasons/{season}/events"
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(mlh_url, headers=headers, timeout=3)
            
            if r.status_code == 200:
                html_content = r.text
                # Simple Regex Scraping for MLH (Event Name & Link)
                # Looking for standard MLH event card structure
                # <a href="..." ... title="Event Name"> ... <p>Date</p> ... </a>
                # Note: MLH structure varies, this is a best-effort scrape
                
                # Regex to find links with titles
                matches = re.findall(r'<a[^>]*href="([^"]+)"[^>]*title="([^"]+)"', html_content)
                
                for href, title in matches[:10]: # Limit to 10
                    # Filter generic links
                    if "mlh.io" in href and "events" not in href: 
                        continue # Skip nav links
                        
                    online_events.append({
                        'title': title,
                        'url': href,
                        'startDate': 'Upcoming (Check Link)', # MLH dates are hard to parse via regex
                        'endDate': '',
                        'host': 'MLH Partner',
                        'city': 'Online/Hybrid'
                    })
        except Exception as e:
            print(f"MLH Scrape Error: {e}")

    # 3. Fallback: Dynamic Mock Data (Always valid relative to NOW)
    if not online_events:
        next_month = (datetime.now() + timedelta(days=30)).strftime('%b')
        online_events = [
            {
                'title': 'Global Innovation Hackathon (Simulated)',
                'url': 'https://devpost.com',
                'startDate': f'{month_name} 28',
                'endDate': f'{month_name} 30',
                'host': 'Tech Community',
                'city': 'Online'
            },
            {
                'title': 'Future Web Challenge (Simulated)',
                'url': 'https://ethglobal.com',
                'startDate': f'{next_month} 05',
                'endDate': f'{next_month} 07',
                'host': 'Web3 Foundation',
                'city': 'Online'
            }
        ]

    # --- Source 2: Dev.to API (Hackathon Articles/News) ---
    devto_events = []
    try:
        devto_url = "https://dev.to/api/articles"
        # Search for 'hackathon' tag
        params = {'tag': 'hackathon', 'per_page': 8, 'state': 'rising'}
        r = requests.get(devto_url, params=params, timeout=3)
        if r.status_code == 200:
            devto_events = r.json()
    except Exception as e:
        print(f"Dev.to API Error: {e}")

    # Fetch Local Events (Admin added)
    local_events = Event.query.all()
    
    return render_template('events.html', online_events=online_events, offline_events=offline_events, local_events=local_events, devto_events=devto_events)

@main_bp.route('/events/delete/<int:id>', methods=['POST'])
@login_required
def delete_event(id):
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))
    
    event = Event.query.get_or_404(id)
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted')
    return redirect(url_for('main.events'))

# --- Quiz (OpenTrivia API) ---
@main_bp.route('/quiz')
@login_required
def quiz():
    # Show history
    history = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.date_played.desc()).all()
    return render_template('quiz_dashboard.html', history=history)

@main_bp.route('/quiz/start')
@login_required
def start_quiz():
    import json
    import random
    import os
    from flask import session
    
    # Load Local Questions (Zero Latency)
    json_path = os.path.join(current_app.root_path, 'static', 'data', 'quiz_data.json')
    try:
        with open(json_path, 'r') as f:
            all_questions = json.load(f)
            
        # Select 10 Random Questions
        selected_questions = random.sample(all_questions, 10)
        
        qt_clean = []
        correct_map = {} # Store correct answers by index
        
        for idx, item in enumerate(selected_questions):
            # Format Matches Template Expectations
            options = item['options']
            random.shuffle(options)
            
            qt_clean.append({
                'id': idx + 1,
                'question': item['question'],
                'options': options,
                'subject': item['subject']
            })
            
            # Map question ID to correct answer
            correct_map[str(idx + 1)] = item['correct_answer']
            
        # Store correct answers in Session
        session['quiz_answers'] = correct_map
        return render_template('quiz_play.html', questions=qt_clean)
        
    except Exception as e:
        flash(f"Error starting quiz: {e}")
        return redirect(url_for('main.quiz'))

@main_bp.route('/quiz/submit', methods=['POST'])
@login_required
def submit_quiz():
    from datetime import date, timedelta
    
    correct_map = session.get('quiz_answers', {})
    if not correct_map:
        flash('Session expired. Please restart quiz.')
        return redirect(url_for('main.quiz'))
        
    score = 0
    total = len(correct_map)
    results_detail = []
    
    for q_id, correct_ans in correct_map.items():
        user_ans = request.values.get(f'q_{q_id}')
        is_correct = (user_ans == correct_ans)
        if is_correct:
            score += 1
            
        results_detail.append({
            'id': q_id,
            'question': f"Question {q_id}", 
            'user_ans': user_ans,
            'correct_ans': correct_ans,
            'is_correct': is_correct
        })
        
    # --- Streak Logic ---
    today = date.today()
    last_played = current_user.last_quiz_date
    
    if last_played == today:
        pass # Already played today, streak stays same
    elif last_played == today - timedelta(days=1):
        current_user.quiz_streak += 1 # Consecutive day
    else:
        current_user.quiz_streak = 1 # Streak broken or new
        
    current_user.last_quiz_date = today
        
    # Save History
    from models import QuizResult
    qr = QuizResult(user_id=current_user.id, score=score, total=total)
    db.session.add(qr)
    db.session.commit()
    
    return render_template('quiz_result.html', score=score, total=total, details=results_detail)

@main_bp.route('/api/spotlight')
@login_required
def spotlight_search():
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
        
    results = []
    
    # 1. Navigation (Static)
    nav_items = [
        {'title': 'Dashboard', 'url': url_for('main.index'), 'type': 'Page'},
        {'title': 'Materials (BCA)', 'url': url_for('main.materials'), 'type': 'Page'},
        {'title': 'Research Hub', 'url': url_for('main.research'), 'type': 'Page'},
        {'title': 'E-Books', 'url': url_for('main.ebooks'), 'type': 'Page'},
        {'title': 'Quiz Arena', 'url': url_for('main.quiz'), 'type': 'Page'},
        {'title': 'Online Hackathons', 'url': url_for('main.events'), 'type': 'Page'},
        {'title': 'My Bookmarks', 'url': url_for('main.bookmarks'), 'type': 'Page'},
    ]
    for item in nav_items:
        if query in item['title'].lower():
            results.append(item)
            
    # 2. Materials (Database)
    materials = Material.query.filter(
        (Material.title.ilike(f'%{query}%')) | 
        (Material.subject.ilike(f'%{query}%'))
    ).limit(5).all()
    
    for m in materials:
        results.append({
            'title': f"{m.title} ({m.subject})",
            'url': f"/static/{m.filepath}", # Direct link to file
            'type': 'Material'
        })
        
    # 3. Events (Database)
    events = Event.query.filter(
        (Event.name.ilike(f'%{query}%')) | 
        (Event.description.ilike(f'%{query}%'))
    ).limit(3).all()
    
    for e in events:
        results.append({
            'title': e.name,
            'url': e.registration_link,
            'type': 'Event'
        })

    # 4. Bookmarks (Database)
    from models import Bookmark
    bookmarks = Bookmark.query.filter(
        Bookmark.title.ilike(f'%{query}%')
    ).filter_by(user_id=current_user.id).limit(3).all()
    
    for b in bookmarks:
        results.append({
            'title': "Bookmark: " + b.title,
            'url': b.link,
            'type': 'Bookmark'
        })
        
    return jsonify(results)






