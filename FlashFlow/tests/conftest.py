"""
Test configuration and fixtures for FlashFlow.
Handles database backup/restore and provides test utilities.
"""

import os
import pytest
from datetime import datetime

# Import the actual app module
import app as app_module


@pytest.fixture
def flask_app():
    """Create and configure a test Flask application."""
    # Store original DB_NAME
    original_db = app_module.DB_NAME
    
    # Configure for testing
    app_module.app.config['TESTING'] = True
    app_module.app.config['WTF_CSRF_ENABLED'] = False
    app_module.app.config['SECRET_KEY'] = 'test_secret_key'
    
    # Use test database
    test_db = 'test_flashcards.db'
    app_module.DB_NAME = test_db
    
    # Create test database
    with app_module.app.app_context():
        app_module.init_db()
        app_module.migrate_db()
    
    yield app_module.app
    
    # Cleanup: restore original DB_NAME
    app_module.DB_NAME = original_db
    
    # Remove test database
    if os.path.exists(test_db):
        os.remove(test_db)


@pytest.fixture
def client(flask_app):
    """A test client for the app."""
    return flask_app.test_client()


@pytest.fixture
def runner(flask_app):
    """A test CLI runner for the app."""
    return flask_app.test_cli_runner()


@pytest.fixture
def db(flask_app):
    """Get database connection."""
    return app_module.get_db_connection()


class TestData:
    """Helper class for creating test data."""
    
    @staticmethod
    def create_teacher(client, username="test_teacher", email="teacher@test.com", password="testpass123"):
        """Create a teacher user."""
        return client.post('/register', data={
            'username': username,
            'email': email,
            'password': password,
            'role': 'teacher'
        }, follow_redirects=True)
    
    @staticmethod
    def create_student(client, username="test_student", email="student@test.com", password="testpass123"):
        """Create a student user."""
        return client.post('/register', data={
            'username': username,
            'email': email,
            'password': password,
            'role': 'student'
        }, follow_redirects=True)
    
    @staticmethod
    def login_user(client, username, password="testpass123"):
        """Login a user."""
        return client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)
    
    @staticmethod
    def create_deck(db, name="Test Deck", user_id=1):
        """Create a deck."""
        cursor = db.execute(
            'INSERT INTO decks (name, created_by) VALUES (?, ?)',
            (name, user_id)
        )
        db.commit()
        return cursor.lastrowid
    
    @staticmethod
    def create_unit(db, name="Test Unit"):
        """Create a unit."""
        cursor = db.execute(
            'INSERT INTO units (name) VALUES (?)',
            (name,)
        )
        db.commit()
        return cursor.lastrowid
    
    @staticmethod
    def create_card(db, deck_id, front, back, unit_id=None, created_by=1):
        """Create a card."""
        if unit_id:
            cursor = db.execute(
                'INSERT INTO cards (deck_id, unit_id, front, back, created_by) VALUES (?, ?, ?, ?, ?)',
                (deck_id, unit_id, front, back, created_by)
            )
        else:
            cursor = db.execute(
                'INSERT INTO cards (deck_id, front, back, created_by) VALUES (?, ?, ?, ?)',
                (deck_id, front, back, created_by)
            )
        db.commit()
        return cursor.lastrowid
    
    @staticmethod
    def create_class(db, name, teacher_id, class_code=None):
        """Create a class."""
        import random
        import string
        if class_code is None:
            class_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        cursor = db.execute(
            'INSERT INTO classes (name, class_code, teacher_id) VALUES (?, ?, ?)',
            (name, class_code, teacher_id)
        )
        db.commit()
        return cursor.lastrowid
    
    @staticmethod
    def enroll_student(db, class_id, student_id):
        """Enroll a student in a class."""
        db.execute(
            'INSERT INTO enrollments (class_id, student_id) VALUES (?, ?)',
            (class_id, student_id)
        )
        db.commit()
    
    @staticmethod
    def assign_card_to_class(db, class_id, card_id, assigned_by):
        """Assign a card to a class."""
        db.execute(
            'INSERT INTO class_cards (class_id, card_id, assigned_by) VALUES (?, ?, ?)',
            (class_id, card_id, assigned_by)
        )
        db.commit()


@pytest.fixture
def test_data():
    """Provide access to test data helpers."""
    return TestData
