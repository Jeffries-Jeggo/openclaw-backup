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
        # Cards table (with unit_id)
        c.execute('''CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            deck_id INTEGER, 
            unit_id INTEGER,
            front TEXT, 
            back TEXT, 
            status TEXT DEFAULT 'new',
            interval INTEGER DEFAULT 0,
            ease REAL DEFAULT 2.5,
            due_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(deck_id) REFERENCES decks(id),
            FOREIGN KEY(unit_id) REFERENCES units(id)
        )''')
        # User progress table (for tracking individual student progress)
        c.execute('''CREATE TABLE IF NOT EXISTS user_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            card_id INTEGER,
            status TEXT DEFAULT 'new',
            interval INTEGER DEFAULT 0,
            ease REAL DEFAULT 2.5,
            due_date TEXT DEFAULT CURRENT_TIMESTAMP,
            last_reviewed TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(card_id) REFERENCES cards(id),
            UNIQUE(user_id, card_id)
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
        
        conn.commit()

# Run migrations on startup
migrate_db()

def get_due_cards(deck_id, user_id=None):
    """Get cards that are due for review based on spaced repetition.
    New cards (status='new') are prioritized and shown first."""
    conn = get_db_connection()
    today = datetime.now().strftime('%Y-%m-%d')
    
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
    
    conn.close()
    return render_template('deck.html', deck=deck, cards=cards, due_count=due_count)

def get_all_units():
    """Get all units for dropdown."""
    conn = get_db_connection()
    units = conn.execute('SELECT * FROM units ORDER BY name ASC').fetchall()
    conn.close()
    return units

@app.route('/deck/<int:deck_id>/add_card', methods=['GET', 'POST'])
@login_required
def add_card(deck_id):
    conn = get_db_connection()
    deck = conn.execute('SELECT * FROM decks WHERE id = ?', (deck_id,)).fetchone()
    
    if not deck:
        conn.close()
        flash('Deck not found.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        front = request.form.get('front', '').strip()
        back = request.form.get('back', '').strip()
        unit_id = request.form.get('unit_id')
        new_unit_name = request.form.get('new_unit_name', '').strip()
        
        if not front or not back:
            flash('Front and back are required.', 'error')
            units = get_all_units()
            conn.close()
            return render_template('add_card.html', deck=deck, units=units)
        
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
            return render_template('add_card.html', deck=deck, units=units)
        
        # Insert the card
        if unit_id and unit_id != 'new':
            conn.execute('INSERT INTO cards (deck_id, unit_id, front, back) VALUES (?, ?, ?, ?)', 
                        (deck_id, unit_id, front, back))
        else:
            conn.execute('INSERT INTO cards (deck_id, front, back) VALUES (?, ?, ?)', 
                        (deck_id, front, back))
        conn.commit()
        conn.close()
        flash('Card added successfully!', 'success')
        return redirect(url_for('view_deck', deck_id=deck_id))
    
    # GET request - show form
    units = conn.execute('SELECT * FROM units ORDER BY name ASC').fetchall()
    conn.close()
    return render_template('add_card.html', deck=deck, units=units)

@app.route('/study/<int:deck_id>')
@login_required
def study(deck_id):
    cards = get_due_cards(deck_id)

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
