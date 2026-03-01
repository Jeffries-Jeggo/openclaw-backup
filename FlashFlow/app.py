from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import csv
import io
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'flashflow_secret_key'
DB_NAME = 'flashcards.db'

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

class User(UserMixin):
    def __init__(self, id, username, email, role):
        self.id = id
        self.username = username
        self.email = email
        self.role = role
    
    def is_teacher(self):
        return self.role == 'teacher'
    
    def is_student(self):
        return self.role == 'student'

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        return User(user['id'], user['username'], user['email'], user['role'])
    return None

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('teacher', 'student')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        # Decks table (modified to include user_id)
        c.execute('''CREATE TABLE IF NOT EXISTS decks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_by INTEGER,
            FOREIGN KEY(created_by) REFERENCES users(id)
        )''')
        # Units table
        c.execute('''CREATE TABLE IF NOT EXISTS units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )''')
        # Cards table (with unit_id and created_by for tracking who made it)
        c.execute('''CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            deck_id INTEGER, 
            unit_id INTEGER,
            created_by INTEGER,
            front TEXT, 
            back TEXT, 
            status TEXT DEFAULT 'new',
            interval INTEGER DEFAULT 0,
            ease REAL DEFAULT 2.5,
            due_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(deck_id) REFERENCES decks(id),
            FOREIGN KEY(unit_id) REFERENCES units(id),
            FOREIGN KEY(created_by) REFERENCES users(id)
        )''')
        # Classes table
        c.execute('''CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            class_code TEXT UNIQUE NOT NULL,
            teacher_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(teacher_id) REFERENCES users(id)
        )''')
        # Enrollments table (students in classes)
        c.execute('''CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER,
            student_id INTEGER,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(class_id) REFERENCES classes(id),
            FOREIGN KEY(student_id) REFERENCES users(id),
            UNIQUE(class_id, student_id)
        )''')
        # Class cards table (cards assigned to classes)
        c.execute('''CREATE TABLE IF NOT EXISTS class_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER,
            card_id INTEGER,
            assigned_by INTEGER,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(class_id) REFERENCES classes(id),
            FOREIGN KEY(card_id) REFERENCES cards(id),
            FOREIGN KEY(assigned_by) REFERENCES users(id),
            UNIQUE(class_id, card_id)
        )''')
        # User progress table (for tracking individual student progress on assigned cards)
        c.execute('''CREATE TABLE IF NOT EXISTS user_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            card_id INTEGER,
            class_id INTEGER,
            status TEXT DEFAULT 'new',
            interval INTEGER DEFAULT 0,
            ease REAL DEFAULT 2.5,
            due_date TEXT DEFAULT CURRENT_TIMESTAMP,
            last_reviewed TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(card_id) REFERENCES cards(id),
            FOREIGN KEY(class_id) REFERENCES classes(id),
            UNIQUE(user_id, card_id, class_id)
        )''')
        conn.commit()

# Initialize DB on startup
if not os.path.exists(DB_NAME):
    init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def migrate_db():
    """Add missing tables/columns to existing database."""
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        
        # Create units table if it doesn't exist
        c.execute('''CREATE TABLE IF NOT EXISTS units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )''')
        
        # Add unit_id column to cards if it doesn't exist
        try:
            c.execute('SELECT unit_id FROM cards LIMIT 1')
        except sqlite3.OperationalError:
            c.execute('ALTER TABLE cards ADD COLUMN unit_id INTEGER REFERENCES units(id)')
        
        # Add created_by column to cards if it doesn't exist
        try:
            c.execute('SELECT created_by FROM cards LIMIT 1')
        except sqlite3.OperationalError:
            c.execute('ALTER TABLE cards ADD COLUMN created_by INTEGER REFERENCES users(id)')
        
        # Create classes table
        c.execute('''CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            class_code TEXT UNIQUE NOT NULL,
            teacher_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(teacher_id) REFERENCES users(id)
        )''')
        
        # Create enrollments table
        c.execute('''CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER,
            student_id INTEGER,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(class_id) REFERENCES classes(id),
            FOREIGN KEY(student_id) REFERENCES users(id),
            UNIQUE(class_id, student_id)
        )''')
        
        # Create class_cards table
        c.execute('''CREATE TABLE IF NOT EXISTS class_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER,
            card_id INTEGER,
            assigned_by INTEGER,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(class_id) REFERENCES classes(id),
            FOREIGN KEY(card_id) REFERENCES cards(id),
            FOREIGN KEY(assigned_by) REFERENCES users(id),
            UNIQUE(class_id, card_id)
        )''')
        
        # Update user_progress table to add class_id if not exists
        try:
            c.execute('SELECT class_id FROM user_progress LIMIT 1')
        except sqlite3.OperationalError:
            c.execute('ALTER TABLE user_progress ADD COLUMN class_id INTEGER REFERENCES classes(id)')
        
        conn.commit()

# Run migrations on startup
migrate_db()

def get_due_cards(deck_id, user_id=None):
    """Get cards that are due for review based on spaced repetition.
    New cards (status='new') are prioritized and shown first.
    For students, only return cards assigned to their enrolled classes."""
    conn = get_db_connection()
    today = datetime.now().strftime('%Y-%m-%d')

    if user_id:
        # Check if user is a student
        user = conn.execute('SELECT role FROM users WHERE id = ?', (user_id,)).fetchone()

        if user and user['role'] == 'student':
            # For students: only get cards assigned to their enrolled classes
            # First, get new cards (prioritize these)
            new_cards = conn.execute('''
                SELECT DISTINCT c.* FROM cards c
                JOIN class_cards cc ON c.id = cc.card_id
                JOIN enrollments e ON cc.class_id = e.class_id
                WHERE c.deck_id = ?
                AND e.student_id = ?
                AND c.status = 'new'
                ORDER BY c.id ASC
            ''', (deck_id, user_id)).fetchall()

            # Then get due review cards
            due_cards = conn.execute('''
                SELECT DISTINCT c.* FROM cards c
                JOIN class_cards cc ON c.id = cc.card_id
                JOIN enrollments e ON cc.class_id = e.class_id
                WHERE c.deck_id = ?
                AND e.student_id = ?
                AND c.status = 'learning'
                AND (c.due_date <= ? OR c.due_date IS NULL OR c.due_date = '')
                ORDER BY c.due_date ASC
            ''', (deck_id, user_id, today)).fetchall()

            conn.close()
            return list(new_cards) + list(due_cards)

    # For teachers or no user_id: get all cards in deck
    # First, get new cards (prioritize these)
    new_cards = conn.execute('''
        SELECT * FROM cards
        WHERE deck_id = ?
        AND status = 'new'
        ORDER BY id ASC
    ''', (deck_id,)).fetchall()

    # Then get due review cards (status='learning' or 'review' with due_date <= today)
    due_cards = conn.execute('''
        SELECT * FROM cards
        WHERE deck_id = ?
        AND status = 'learning'
        AND (due_date <= ? OR due_date IS NULL OR due_date = '')
        ORDER BY due_date ASC
    ''', (deck_id, today)).fetchall()

    conn.close()

    # Return new cards first, then due cards
    return list(new_cards) + list(due_cards)

# ==================== AUTH ROUTES ====================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password')
        role = request.form.get('role', 'student')
        
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return redirect(url_for('register'))
        
        if role not in ['teacher', 'student']:
            flash('Invalid role selected.', 'error')
            return redirect(url_for('register'))
        
        password_hash = generate_password_hash(password)
        
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)',
                        (username, email, password_hash, role))
            conn.commit()
            conn.close()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'error')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            user_obj = User(user['id'], user['username'], user['email'], user['role'])
            login_user(user_obj, remember=True)
            flash(f'Welcome back, {user["username"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

# ==================== MAIN APP ROUTES ====================

@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    decks = conn.execute('SELECT * FROM decks').fetchall()
    conn.close()
    return render_template('index.html', decks=decks)

@app.route('/create_deck', methods=['POST'])
@login_required
def create_deck():
    name = request.form.get('name')
    if name:
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO decks (name, created_by) VALUES (?, ?)', 
                        (name, current_user.id))
            conn.commit()
            conn.close()
            flash(f'Deck "{name}" created!', 'success')
        except sqlite3.IntegrityError:
            flash('Deck already exists!', 'error')
    return redirect(url_for('index'))

@app.route('/deck/<int:deck_id>')
@login_required
def view_deck(deck_id):
    conn = get_db_connection()
    deck = conn.execute('SELECT * FROM decks WHERE id = ?', (deck_id,)).fetchone()

    if not deck:
        conn.close()
        flash('Deck not found.', 'error')
        return redirect(url_for('index'))

    cards = conn.execute('''
        SELECT cards.*, units.name as unit_name
        FROM cards
        LEFT JOIN units ON cards.unit_id = units.id
        WHERE cards.deck_id = ?
    ''', (deck_id,)).fetchall()

    # Count due cards (including new cards and learning cards that are due)
    today = datetime.now().strftime('%Y-%m-%d')
    due_count = conn.execute('''
        SELECT COUNT(*) FROM cards
        WHERE deck_id = ?
        AND status != 'known'
        AND (
            status = 'new'
            OR (status = 'learning' AND (due_date <= ? OR due_date IS NULL OR due_date = ''))
        )
    ''', (deck_id, today)).fetchone()[0]

    # Get teacher's classes for bulk assignment
    teacher_classes = []
    if current_user.is_teacher():
        teacher_classes = conn.execute(
            'SELECT * FROM classes WHERE teacher_id = ? ORDER BY name ASC',
            (current_user.id,)
        ).fetchall()

    conn.close()
    return render_template('deck.html', deck=deck, cards=cards, due_count=due_count, teacher_classes=teacher_classes)


@app.route('/deck/<int:deck_id>/assign_cards', methods=['POST'])
@login_required
def bulk_assign_from_deck(deck_id):
    """Assign multiple cards to a class."""
    if not current_user.is_teacher():
        flash('Only teachers can assign cards.', 'error')
        return redirect(url_for('view_deck', deck_id=deck_id))

    card_ids = request.form.getlist('card_ids')
    class_id = request.form.get('class_id')

    if not card_ids:
        flash('No cards selected.', 'error')
        return redirect(url_for('view_deck', deck_id=deck_id))

    if not class_id:
        flash('Please select a class.', 'error')
        return redirect(url_for('view_deck', deck_id=deck_id))

    conn = get_db_connection()

    # Verify teacher owns this class
    class_check = conn.execute(
        'SELECT id FROM classes WHERE id = ? AND teacher_id = ?',
        (class_id, current_user.id)
    ).fetchone()

    if not class_check:
        conn.close()
        flash('Invalid class selected.', 'error')
        return redirect(url_for('view_deck', deck_id=deck_id))

    # Assign cards to class
    assigned_count = 0
    for card_id in card_ids:
        try:
            conn.execute(
                'INSERT INTO class_cards (class_id, card_id, assigned_by) VALUES (?, ?, ?)',
                (class_id, card_id, current_user.id)
            )
            assigned_count += 1

            # Initialize user_progress for all students in the class
            students = conn.execute(
                'SELECT student_id FROM enrollments WHERE class_id = ?',
                (class_id,)
            ).fetchall()
            for student in students:
                conn.execute('''
                    INSERT OR IGNORE INTO user_progress
                    (user_id, card_id, class_id, status, due_date)
                    VALUES (?, ?, ?, 'new', CURRENT_TIMESTAMP)
                ''', (student['student_id'], card_id, class_id))
        except sqlite3.IntegrityError:
            pass  # Already assigned

    conn.commit()
    conn.close()

    flash(f'{assigned_count} card(s) assigned to class!', 'success')
    return redirect(url_for('view_deck', deck_id=deck_id))

def get_all_units():
    """Get all units for dropdown."""
    conn = get_db_connection()
    units = conn.execute('SELECT * FROM units ORDER BY name ASC').fetchall()
    conn.close()
    return units

def get_teacher_classes(teacher_id):
    """Get all classes created by a teacher."""
    conn = get_db_connection()
    classes = conn.execute(
        'SELECT * FROM classes WHERE teacher_id = ? ORDER BY name ASC',
        (teacher_id,)
    ).fetchall()
    conn.close()
    return classes

def get_student_classes(student_id):
    """Get all classes a student is enrolled in."""
    conn = get_db_connection()
    classes = conn.execute('''
        SELECT c.* FROM classes c
        JOIN enrollments e ON c.id = e.class_id
        WHERE e.student_id = ?
        ORDER BY c.name ASC
    ''', (student_id,)).fetchall()
    conn.close()
    return classes

@app.route('/deck/<int:deck_id>/add_card', methods=['GET', 'POST'])
@login_required
def add_card(deck_id):
    conn = get_db_connection()
    deck = conn.execute('SELECT * FROM decks WHERE id = ?', (deck_id,)).fetchone()
    
    if not deck:
        conn.close()
        flash('Deck not found.', 'error')
        return redirect(url_for('index'))
    
    # Get teacher's classes for assignment (only for teachers)
    teacher_classes = []
    if current_user.is_teacher():
        teacher_classes = conn.execute(
            'SELECT * FROM classes WHERE teacher_id = ? ORDER BY name ASC',
            (current_user.id,)
        ).fetchall()
    
    if request.method == 'POST':
        front = request.form.get('front', '').strip()
        back = request.form.get('back', '').strip()
        unit_id = request.form.get('unit_id')
        new_unit_name = request.form.get('new_unit_name', '').strip()
        class_ids = request.form.getlist('class_ids')  # Get multiple class assignments
        
        if not front or not back:
            flash('Front and back are required.', 'error')
            units = get_all_units()
            conn.close()
            return render_template('add_card.html', deck=deck, units=units, teacher_classes=teacher_classes)
        
        # Handle new unit creation
        if unit_id == 'new' and new_unit_name:
            try:
                cursor = conn.execute('INSERT INTO units (name) VALUES (?)', (new_unit_name,))
                unit_id = cursor.lastrowid
                conn.commit()
                flash(f'New unit "{new_unit_name}" created!', 'success')
            except sqlite3.IntegrityError:
                # Unit already exists, get its ID
                existing = conn.execute('SELECT id FROM units WHERE name = ?', (new_unit_name,)).fetchone()
                unit_id = existing['id']
                flash(f'Using existing unit "{new_unit_name}".', 'info')
        elif unit_id == 'new':
            flash('Please enter a name for the new unit.', 'error')
            units = get_all_units()
            conn.close()
            return render_template('add_card.html', deck=deck, units=units, teacher_classes=teacher_classes)
        
        # Insert the card with created_by
        if unit_id and unit_id != 'new':
            cursor = conn.execute(
                'INSERT INTO cards (deck_id, unit_id, front, back, created_by) VALUES (?, ?, ?, ?, ?)', 
                (deck_id, unit_id, front, back, current_user.id))
        else:
            cursor = conn.execute(
                'INSERT INTO cards (deck_id, front, back, created_by) VALUES (?, ?, ?, ?)', 
                (deck_id, front, back, current_user.id))
        card_id = cursor.lastrowid
        conn.commit()
        
        # Assign card to selected classes
        if class_ids and current_user.is_teacher():
            assigned_count = 0
            for class_id in class_ids:
                # Verify teacher owns this class
                class_check = conn.execute(
                    'SELECT id FROM classes WHERE id = ? AND teacher_id = ?',
                    (class_id, current_user.id)
                ).fetchone()
                if class_check:
                    try:
                        conn.execute(
                            'INSERT INTO class_cards (class_id, card_id, assigned_by) VALUES (?, ?, ?)',
                            (class_id, card_id, current_user.id)
                        )
                        assigned_count += 1
                        
                        # Initialize user_progress for all students in the class
                        students = conn.execute(
                            'SELECT student_id FROM enrollments WHERE class_id = ?',
                            (class_id,)
                        ).fetchall()
                        for student in students:
                            conn.execute('''
                                INSERT OR IGNORE INTO user_progress 
                                (user_id, card_id, class_id, status, due_date)
                                VALUES (?, ?, ?, 'new', CURRENT_TIMESTAMP)
                            ''', (student['student_id'], card_id, class_id))
                    except sqlite3.IntegrityError:
                        pass  # Already assigned
            conn.commit()
            if assigned_count > 0:
                flash(f'Card assigned to {assigned_count} class(es)!', 'success')
        
        conn.close()
        flash('Card added successfully!', 'success')
        return redirect(url_for('view_deck', deck_id=deck_id))
    
    # GET request - show form
    units = conn.execute('SELECT * FROM units ORDER BY name ASC').fetchall()
    conn.close()
    return render_template('add_card.html', deck=deck, units=units, teacher_classes=teacher_classes)

@app.route('/study/<int:deck_id>')
@login_required
def study(deck_id):
    cards = get_due_cards(deck_id, current_user.id)

    if not cards:
        flash('No cards due for review! Great job! 🎉', 'success')
        return redirect(url_for('view_deck', deck_id=deck_id))

    card = cards[0]
    return render_template('study.html', card=card, deck_id=deck_id, cards_remaining=len(cards))

@app.route('/study/<int:deck_id>/rate', methods=['POST'])
@login_required
def rate_card(deck_id):
    card_id = request.form.get('card_id')
    rating = request.form.get('status')

    conn = get_db_connection()
    card = conn.execute('SELECT * FROM cards WHERE id = ?', (card_id,)).fetchone()

    interval = card['interval'] if card['interval'] else 0
    ease = card['ease'] if card['ease'] else 2.5

    rating_map = {'again': 0, 'hard': 1, 'good': 2, 'easy': 3}
    score = rating_map.get(rating, 2)

    if score < 2:
        interval = 0
    else:
        if interval == 0:
            interval = 1
        elif interval == 1:
            interval = 6
        else:
            interval = int(interval * ease)

        ease = ease + (0.1 - (3 - score) * (0.08 + (3 - score) * 0.02))
        if ease < 1.3:
            ease = 1.3

    due_date = datetime.now() + timedelta(days=interval)
    due_date_str = due_date.strftime('%Y-%m-%d')

    new_status = 'learning' if score < 2 else 'learning'

    conn.execute('''
        UPDATE cards
        SET interval = ?, ease = ?, due_date = ?, status = ?
        WHERE id = ?
    ''', (interval, ease, due_date_str, new_status, card_id))

    # Also update user_progress if this card is assigned to any of user's classes
    if current_user.is_student():
        conn.execute('''
            UPDATE user_progress
            SET interval = ?, ease = ?, due_date = ?, status = ?, last_reviewed = CURRENT_TIMESTAMP
            WHERE user_id = ? AND card_id = ?
        ''', (interval, ease, due_date_str, new_status, current_user.id, card_id))

    conn.commit()
    conn.close()

    return redirect(url_for('study', deck_id=deck_id))

@app.route('/deck/<int:deck_id>/export')
@login_required
def export_deck(deck_id):
    conn = get_db_connection()
    cards = conn.execute('SELECT front, back, status, interval, ease FROM cards WHERE deck_id = ?', (deck_id,)).fetchall()
    deck = conn.execute('SELECT name FROM decks WHERE id = ?', (deck_id,)).fetchone()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['front', 'back', 'status', 'interval', 'ease'])
    
    for card in cards:
        writer.writerow([card['front'], card['back'], card['status'], card['interval'], card['ease']])
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={deck["name"]}_cards.csv'}
    )

@app.route('/deck/<int:deck_id>/import', methods=['POST'])
@login_required
def import_cards(deck_id):
    if 'file' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('view_deck', deck_id=deck_id))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('view_deck', deck_id=deck_id))
    
    if file:
        try:
            stream = io.StringIO(file.stream.read().decode('UTF-8'), newline=None)
            csv_reader = csv.reader(stream)
            next(csv_reader)
            
            conn = get_db_connection()
            count = 0
            for row in csv_reader:
                if len(row) >= 2:
                    front = row[0].strip()
                    back = row[1].strip()
                    if front and back:
                        conn.execute('INSERT INTO cards (deck_id, front, back) VALUES (?, ?, ?)', 
                                   (deck_id, front, back))
                        count += 1
            conn.commit()
            conn.close()
            
            flash(f'Imported {count} cards!', 'success')
        except Exception as e:
            flash(f'Error importing: {str(e)}', 'error')
    
    return redirect(url_for('view_deck', deck_id=deck_id))

# ==================== CLASS MANAGEMENT ====================

def generate_class_code(length=6):
    """Generate a random class code (uppercase letters + numbers)."""
    import random
    import string
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@app.route('/classes')
@login_required
def list_classes():
    """List classes for teacher or student."""
    conn = get_db_connection()
    
    if current_user.is_teacher():
        # Get teacher's classes
        classes = conn.execute('''
            SELECT c.*, COUNT(e.student_id) as student_count
            FROM classes c
            LEFT JOIN enrollments e ON c.id = e.class_id
            WHERE c.teacher_id = ?
            GROUP BY c.id
            ORDER BY c.created_at DESC
        ''', (current_user.id,)).fetchall()
        
        conn.close()
        
        if not classes:
            flash('No classes yet. Create your first class!', 'info')
            return redirect(url_for('create_class'))
        
        return render_template('teacher_classes.html', classes=classes)
    else:
        # Get student's enrolled classes
        classes = conn.execute('''
            SELECT c.*, u.username as teacher_name
            FROM classes c
            JOIN enrollments e ON c.id = e.class_id
            JOIN users u ON c.teacher_id = u.id
            WHERE e.student_id = ?
            ORDER BY c.created_at DESC
        ''', (current_user.id,)).fetchall()
        
        conn.close()
        return render_template('student_classes.html', classes=classes)

@app.route('/classes/new', methods=['GET', 'POST'])
@login_required
def create_class():
    """Create a new class (teachers only)."""
    if not current_user.is_teacher():
        flash('Only teachers can create classes.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        class_name = request.form.get('name', '').strip()
        
        if not class_name:
            flash('Class name is required.', 'error')
            return render_template('create_class.html')
        
        # Generate unique class code
        conn = get_db_connection()
        while True:
            class_code = generate_class_code()
            existing = conn.execute('SELECT id FROM classes WHERE class_code = ?', (class_code,)).fetchone()
            if not existing:
                break
        
        try:
            conn.execute(
                'INSERT INTO classes (name, class_code, teacher_id) VALUES (?, ?, ?)',
                (class_name, class_code, current_user.id)
            )
            conn.commit()
            flash(f'Class "{class_name}" created! Class code: {class_code}', 'success')
        except Exception as e:
            flash(f'Error creating class: {str(e)}', 'error')
        finally:
            conn.close()
        
        return redirect(url_for('list_classes'))
    
    return render_template('create_class.html')

@app.route('/classes/join', methods=['GET', 'POST'])
@login_required
def join_class():
    """Join a class (students only)."""
    if current_user.is_teacher():
        flash('Teachers cannot join classes. Students join your classes instead.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        class_code = request.form.get('class_code', '').strip().upper()
        
        if not class_code:
            flash('Class code is required.', 'error')
            return render_template('join_class.html')
        
        conn = get_db_connection()
        
        # Find class by code
        class_info = conn.execute('SELECT * FROM classes WHERE class_code = ?', (class_code,)).fetchone()
        
        if not class_info:
            conn.close()
            flash('Invalid class code.', 'error')
            return render_template('join_class.html')
        
        # Check if already enrolled
        existing = conn.execute(
            'SELECT id FROM enrollments WHERE class_id = ? AND student_id = ?',
            (class_info['id'], current_user.id)
        ).fetchone()
        
        if existing:
            conn.close()
            flash('You are already enrolled in this class.', 'info')
            return redirect(url_for('list_classes'))
        
        # Enroll student
        try:
            conn.execute(
                'INSERT INTO enrollments (class_id, student_id) VALUES (?, ?)',
                (class_info['id'], current_user.id)
            )
            conn.commit()
            flash(f'Successfully joined "{class_info["name"]}"!', 'success')
        except Exception as e:
            flash(f'Error joining class: {str(e)}', 'error')
        finally:
            conn.close()
        
        return redirect(url_for('list_classes'))
    
    return render_template('join_class.html')

@app.route('/classes/<int:class_id>/assign', methods=['GET', 'POST'])
@login_required
def assign_cards_to_class(class_id):
    """Assign cards to a class from the class view."""
    if not current_user.is_teacher():
        flash('Only teachers can assign cards.', 'error')
        return redirect(url_for('index'))

    conn = get_db_connection()

    # Verify teacher owns this class
    class_info = conn.execute(
        'SELECT * FROM classes WHERE id = ? AND teacher_id = ?',
        (class_id, current_user.id)
    ).fetchone()

    if not class_info:
        conn.close()
        flash('Class not found or access denied.', 'error')
        return redirect(url_for('list_classes'))

    if request.method == 'POST':
        card_ids = request.form.getlist('card_ids')
        
        if not card_ids:
            flash('No cards selected.', 'error')
            conn.close()
            return redirect(url_for('assign_cards_to_class', class_id=class_id))

        # Assign cards to class
        assigned_count = 0
        for card_id in card_ids:
            try:
                conn.execute(
                    'INSERT INTO class_cards (class_id, card_id, assigned_by) VALUES (?, ?, ?)',
                    (class_id, card_id, current_user.id)
                )
                assigned_count += 1

                # Initialize user_progress for all students in the class
                students = conn.execute(
                    'SELECT student_id FROM enrollments WHERE class_id = ?',
                    (class_id,)
                ).fetchall()
                for student in students:
                    conn.execute('''
                        INSERT OR IGNORE INTO user_progress 
                        (user_id, card_id, class_id, status, due_date)
                        VALUES (?, ?, ?, 'new', CURRENT_TIMESTAMP)
                    ''', (student['student_id'], card_id, class_id))
            except sqlite3.IntegrityError:
                pass  # Already assigned

        conn.commit()
        conn.close()

        flash(f'{assigned_count} card(s) assigned to class!', 'success')
        return redirect(url_for('list_classes'))

    # GET request - show available cards
    # Get all decks and cards created by this teacher
    decks = conn.execute('''
        SELECT d.* FROM decks d
        WHERE d.created_by = ?
        ORDER BY d.name ASC
    ''', (current_user.id,)).fetchall()

    deck_cards = {}
    for deck in decks:
        cards = conn.execute('''
            SELECT c.id, c.front, c.back, u.name as unit_name,
                   (SELECT COUNT(*) FROM class_cards cc WHERE cc.card_id = c.id AND cc.class_id = ?) as is_assigned
            FROM cards c
            LEFT JOIN units u ON c.unit_id = u.id
            WHERE c.deck_id = ? AND c.created_by = ?
            ORDER BY c.id DESC
        ''', (class_id, deck['id'], current_user.id)).fetchall()
        if cards:
            deck_cards[deck] = cards

    conn.close()
    
    return render_template('assign_cards_to_class.html', 
                           class_info=class_info, 
                           deck_cards=deck_cards)

@app.route('/classes/<int:class_id>/dashboard')
@login_required
def class_dashboard(class_id):
    """Teacher dashboard for a class with student progress stats."""
    if not current_user.is_teacher():
        flash('Only teachers can access class dashboards.', 'error')
        return redirect(url_for('index'))

    conn = get_db_connection()

    # Verify teacher owns this class
    class_info = conn.execute(
        'SELECT * FROM classes WHERE id = ? AND teacher_id = ?',
        (class_id, current_user.id)
    ).fetchone()

    if not class_info:
        conn.close()
        flash('Class not found or access denied.', 'error')
        return redirect(url_for('list_classes'))

    # Get filter parameters
    unit_filter = request.args.get('unit', '')
    student_filter = request.args.get('student', '')

    # Get all units for filter dropdown
    units = conn.execute('''
        SELECT DISTINCT u.id, u.name FROM units u
        JOIN cards c ON u.id = c.unit_id
        JOIN class_cards cc ON c.id = cc.card_id
        WHERE cc.class_id = ?
        ORDER BY u.name ASC
    ''', (class_id,)).fetchall()

    # Get all students in class for filter dropdown
    students = conn.execute('''
        SELECT u.id, u.username FROM users u
        JOIN enrollments e ON u.id = e.student_id
        WHERE e.class_id = ?
        ORDER BY u.username ASC
    ''', (class_id,)).fetchall()

    # Build student progress query
    query = '''
        SELECT
            u.id as student_id,
            u.username,
            c.id as card_id,
            c.front,
            c.back,
            un.id as unit_id,
            un.name as unit_name,
            up.status,
            up.interval,
            up.ease,
            up.due_date,
            up.last_reviewed
        FROM users u
        JOIN enrollments e ON u.id = e.student_id
        JOIN class_cards cc ON e.class_id = cc.class_id
        JOIN cards c ON cc.card_id = c.id
        LEFT JOIN units un ON c.unit_id = un.id
        LEFT JOIN user_progress up ON u.id = up.user_id AND c.id = up.card_id AND up.class_id = cc.class_id
        WHERE e.class_id = ?
    '''
    params = [class_id]

    if unit_filter:
        query += ' AND un.id = ?'
        params.append(unit_filter)

    if student_filter:
        query += ' AND u.id = ?'
        params.append(student_filter)

    query += ' ORDER BY u.username, un.name, c.id'

    progress_data = conn.execute(query, params).fetchall()

    # Calculate statistics
    stats = {
        'total_students': len(set(p['student_id'] for p in progress_data)),
        'total_cards': len(set(p['card_id'] for p in progress_data)),
        'cards_due': 0,
        'completed_cards': 0,
        'total_ease': 0,
        'ease_count': 0
    }

    today = datetime.now().strftime('%Y-%m-%d')
    student_stats = {}

    for p in progress_data:
        student_id = p['student_id']
        if student_id not in student_stats:
            student_stats[student_id] = {
                'username': p['username'],
                'cards_total': 0,
                'cards_due': 0,
                'cards_completed': 0,
                'total_ease': 0,
                'ease_count': 0
            }

        student_stats[student_id]['cards_total'] += 1

        # Count due cards
        if p['status'] == 'new' or (p['status'] == 'learning' and p['due_date'] and p['due_date'] <= today):
            student_stats[student_id]['cards_due'] += 1
            stats['cards_due'] += 1

        # Count completed (reviewed at least once)
        if p['last_reviewed']:
            student_stats[student_id]['cards_completed'] += 1
            stats['completed_cards'] += 1

        # Track ease for average
        if p['ease']:
            student_stats[student_id]['total_ease'] += p['ease']
            student_stats[student_id]['ease_count'] += 1
            stats['total_ease'] += p['ease']
            stats['ease_count'] += 1

    # Calculate completion rate
    if stats['total_cards'] > 0 and stats['total_students'] > 0:
        stats['completion_rate'] = round((stats['completed_cards'] / (stats['total_cards'] * stats['total_students'])) * 100, 1)
    else:
        stats['completion_rate'] = 0

    # Calculate average ease
    if stats['ease_count'] > 0:
        stats['avg_ease'] = round(stats['total_ease'] / stats['ease_count'], 2)
    else:
        stats['avg_ease'] = 2.5

    # Calculate per-student completion rates
    for student_id, sstats in student_stats.items():
        if sstats['cards_total'] > 0:
            sstats['completion_rate'] = round((sstats['cards_completed'] / sstats['cards_total']) * 100, 1)
        else:
            sstats['completion_rate'] = 0

        if sstats['ease_count'] > 0:
            sstats['avg_ease'] = round(sstats['total_ease'] / sstats['ease_count'], 2)
        else:
            sstats['avg_ease'] = 2.5

    conn.close()

    return render_template(
        'class_dashboard.html',
        class_info=class_info,
        units=units,
        students=students,
        student_stats=student_stats,
        stats=stats,
        unit_filter=unit_filter,
        student_filter=student_filter
    )


@app.route('/classes/<int:class_id>/study')
@login_required
def study_class(class_id):
    """Student study view for class cards."""
    if not current_user.is_student():
        flash('Only students can study class cards.', 'error')
        return redirect(url_for('index'))

    conn = get_db_connection()

    # Verify student is enrolled in this class
    enrollment = conn.execute(
        'SELECT id FROM enrollments WHERE class_id = ? AND student_id = ?',
        (class_id, current_user.id)
    ).fetchone()

    if not enrollment:
        conn.close()
        flash('You are not enrolled in this class.', 'error')
        return redirect(url_for('list_classes'))

    # Get class info
    class_info = conn.execute('''
        SELECT c.*, u.username as teacher_name
        FROM classes c
        JOIN users u ON c.teacher_id = u.id
        WHERE c.id = ?
    ''', (class_id,)).fetchone()

    # Get cards assigned to this class that are due for the student
    today = datetime.now().strftime('%Y-%m-%d')

    # Get new cards first
    new_cards = conn.execute('''
        SELECT c.*, un.name as unit_name, up.status as progress_status
        FROM cards c
        JOIN class_cards cc ON c.id = cc.card_id
        LEFT JOIN units un ON c.unit_id = un.id
        LEFT JOIN user_progress up ON c.id = up.card_id AND up.user_id = ? AND up.class_id = ?
        WHERE cc.class_id = ?
        AND (up.status IS NULL OR up.status = 'new')
        ORDER BY c.id ASC
    ''', (current_user.id, class_id, class_id)).fetchall()

    # Get due review cards
    due_cards = conn.execute('''
        SELECT c.*, un.name as unit_name, up.status as progress_status
        FROM cards c
        JOIN class_cards cc ON c.id = cc.card_id
        LEFT JOIN units un ON c.unit_id = un.id
        LEFT JOIN user_progress up ON c.id = up.card_id AND up.user_id = ? AND up.class_id = ?
        WHERE cc.class_id = ?
        AND up.status = 'learning'
        AND (up.due_date <= ? OR up.due_date IS NULL OR up.due_date = '')
        ORDER BY up.due_date ASC
    ''', (current_user.id, class_id, class_id, today)).fetchall()

    cards = list(new_cards) + list(due_cards)
    conn.close()

    if not cards:
        flash('No cards due for review in this class! Great job! 🎉', 'success')
        return redirect(url_for('list_classes'))

    card = cards[0]
    return render_template('study_class.html', card=card, class_id=class_id, class_info=class_info, cards_remaining=len(cards))


@app.route('/classes/<int:class_id>/rate', methods=['POST'])
@login_required
def rate_class_card(class_id):
    """Rate a card during class study session."""
    if not current_user.is_student():
        flash('Only students can rate class cards.', 'error')
        return redirect(url_for('index'))

    card_id = request.form.get('card_id')
    rating = request.form.get('status')

    conn = get_db_connection()

    # Get current progress
    progress = conn.execute('''
        SELECT * FROM user_progress
        WHERE user_id = ? AND card_id = ? AND class_id = ?
    ''', (current_user.id, card_id, class_id)).fetchone()

    if progress:
        interval = progress['interval'] if progress['interval'] else 0
        ease = progress['ease'] if progress['ease'] else 2.5
    else:
        interval = 0
        ease = 2.5

    rating_map = {'again': 0, 'hard': 1, 'good': 2, 'easy': 3}
    score = rating_map.get(rating, 2)

    if score < 2:
        interval = 0
    else:
        if interval == 0:
            interval = 1
        elif interval == 1:
            interval = 6
        else:
            interval = int(interval * ease)

        ease = ease + (0.1 - (3 - score) * (0.08 + (3 - score) * 0.02))
        if ease < 1.3:
            ease = 1.3

    due_date = datetime.now() + timedelta(days=interval)
    due_date_str = due_date.strftime('%Y-%m-%d')

    new_status = 'learning' if score < 2 else 'learning'

    # Update or insert user progress
    conn.execute('''
        INSERT INTO user_progress (user_id, card_id, class_id, interval, ease, due_date, status, last_reviewed)
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id, card_id, class_id) DO UPDATE SET
            interval = excluded.interval,
            ease = excluded.ease,
            due_date = excluded.due_date,
            status = excluded.status,
            last_reviewed = CURRENT_TIMESTAMP
    ''', (current_user.id, card_id, class_id, interval, ease, due_date_str, new_status))

    conn.commit()
    conn.close()

    return redirect(url_for('study_class', class_id=class_id))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
