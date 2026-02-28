from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
import sqlite3
import os
import csv
import io
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'flashflow_secret_key'
DB_NAME = 'flashcards.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS decks (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)''')
        c.execute('''CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            deck_id INTEGER, 
            front TEXT, 
            back TEXT, 
            status TEXT DEFAULT 'new',
            interval INTEGER DEFAULT 0,
            ease REAL DEFAULT 2.5,
            due_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(deck_id) REFERENCES decks(id)
        )''')
        conn.commit()

# Initialize DB on startup
if not os.path.exists(DB_NAME):
    init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def get_due_cards(deck_id):
    """Get cards that are due for review based on spaced repetition."""
    conn = get_db_connection()
    today = datetime.now().strftime('%Y-%m-%d')
    # Get cards where due_date <= today OR status is 'new'/'learning' with no due date set
    cards = conn.execute('''
        SELECT * FROM cards 
        WHERE deck_id = ? 
        AND (due_date <= ? OR due_date IS NULL OR due_date = '')
        AND status != 'known'
    ''', (deck_id, today)).fetchall()
    conn.close()
    return cards

@app.route('/')
def index():
    conn = get_db_connection()
    decks = conn.execute('SELECT * FROM decks').fetchall()
    conn.close()
    return render_template('index.html', decks=decks)

@app.route('/create_deck', methods=['POST'])
def create_deck():
    name = request.form.get('name')
    if name:
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO decks (name) VALUES (?)', (name,))
            conn.commit()
            conn.close()
            flash(f'Deck "{name}" created!', 'success')
        except sqlite3.IntegrityError:
            flash('Deck already exists!', 'error')
    return redirect(url_for('index'))

@app.route('/deck/<int:deck_id>')
def view_deck(deck_id):
    conn = get_db_connection()
    deck = conn.execute('SELECT * FROM decks WHERE id = ?', (deck_id,)).fetchone()
    cards = conn.execute('SELECT * FROM cards WHERE deck_id = ?', (deck_id,)).fetchall()
    
    # Count due cards
    today = datetime.now().strftime('%Y-%m-%d')
    due_count = conn.execute('''
        SELECT COUNT(*) FROM cards 
        WHERE deck_id = ? 
        AND (due_date <= ? OR due_date IS NULL OR due_date = '')
        AND status != 'known'
    ''', (deck_id, today)).fetchone()[0]
    
    conn.close()
    return render_template('deck.html', deck=deck, cards=cards, due_count=due_count)

@app.route('/add_card', methods=['POST'])
def add_card():
    deck_id = request.form.get('deck_id')
    front = request.form.get('front')
    back = request.form.get('back')
    if deck_id and front and back:
        conn = get_db_connection()
        conn.execute('INSERT INTO cards (deck_id, front, back) VALUES (?, ?, ?)', (deck_id, front, back))
        conn.commit()
        conn.close()
        flash('Card added!', 'success')
    return redirect(url_for('view_deck', deck_id=deck_id))

@app.route('/study/<int:deck_id>')
def study(deck_id):
    cards = get_due_cards(deck_id)

    if not cards:
        flash('No cards due for review! Great job! 🎉', 'success')
        return redirect(url_for('view_deck', deck_id=deck_id))

    # Pick the first due card
    card = cards[0]
    return render_template('study.html', card=card, deck_id=deck_id, cards_remaining=len(cards))

@app.route('/study/<int:deck_id>/rate', methods=['POST'])
def rate_card(deck_id):
    card_id = request.form.get('card_id')
    rating = request.form.get('status')  # 'again', 'hard', 'good', 'easy'
    
    conn = get_db_connection()
    card = conn.execute('SELECT * FROM cards WHERE id = ?', (card_id,)).fetchone()
    
    # SM-2 Algorithm implementation
    interval = card['interval'] if card['interval'] else 0
    ease = card['ease'] if card['ease'] else 2.5
    
    # Rating mappings: again=0, hard=1, good=2, easy=3
    rating_map = {'again': 0, 'hard': 1, 'good': 2, 'easy': 3}
    score = rating_map.get(rating, 2)
    
    if score < 2:
        # Failed - reset interval
        interval = 0
    else:
        # Success - increase interval
        if interval == 0:
            interval = 1
        elif interval == 1:
            interval = 6
        else:
            interval = int(interval * ease)
        
        # Adjust ease factor
        ease = ease + (0.1 - (3 - score) * (0.08 + (3 - score) * 0.02))
        if ease < 1.3:
            ease = 1.3
    
    # Calculate next due date
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
def export_deck(deck_id):
    """Export all cards in a deck to CSV."""
    conn = get_db_connection()
    cards = conn.execute('SELECT front, back, status, interval, ease FROM cards WHERE deck_id = ?', (deck_id,)).fetchall()
    deck = conn.execute('SELECT name FROM decks WHERE id = ?', (deck_id,)).fetchone()
    conn.close()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['front', 'back', 'status', 'interval', 'ease'])
    
    for card in cards:
        writer.writerow([card['front'], card['back'], card['status'], card['interval'], card['ease']])
    
    # Return as downloadable file
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={deck["name"]}_cards.csv'}
    )

@app.route('/deck/<int:deck_id>/import', methods=['POST'])
def import_cards(deck_id):
    """Import cards from CSV file."""
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
            next(csv_reader)  # Skip header row
            
            conn = get_db_connection()
            count = 0
            for row in csv_reader:
                if len(row) >= 2:  # At least front and back
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