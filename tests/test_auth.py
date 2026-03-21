"""
Test authentication: registration, login, logout, roles.
"""
import pytest


@pytest.mark.auth
class TestRegistration:
    """Test user registration."""
    
    def test_teacher_registration_success(self, client):
        """Test successful teacher registration."""
        response = client.post('/register', data={
            'username': 'new_teacher',
            'email': 'newteacher@test.com',
            'password': 'securepass123',
            'role': 'teacher'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Registration successful' in response.data or b'Log In' in response.data
    
    def test_student_registration_success(self, client):
        """Test successful student registration."""
        response = client.post('/register', data={
            'username': 'new_student',
            'email': 'newstudent@test.com',
            'password': 'securepass123',
            'role': 'student'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Registration successful' in response.data or b'Log In' in response.data
    
    def test_registration_duplicate_username(self, client, test_data):
        """Test registration fails with duplicate username."""
        # Create first user
        test_data.create_teacher(client, username='duplicate_user')
        
        # Try to create second user with same username
        response = client.post('/register', data={
            'username': 'duplicate_user',
            'email': 'different@test.com',
            'password': 'securepass123',
            'role': 'teacher'
        }, follow_redirects=True)
        
        assert b'Username or email already exists' in response.data
    
    def test_registration_duplicate_email(self, client, test_data):
        """Test registration fails with duplicate email."""
        # Create first user
        test_data.create_teacher(client, email='duplicate@test.com')
        
        # Try to create second user with same email
        response = client.post('/register', data={
            'username': 'different_user',
            'email': 'duplicate@test.com',
            'password': 'securepass123',
            'role': 'teacher'
        }, follow_redirects=True)
        
        assert b'Username or email already exists' in response.data
    
    def test_registration_missing_fields(self, client):
        """Test registration fails with missing fields."""
        response = client.post('/register', data={
            'username': '',
            'email': 'test@test.com',
            'password': 'securepass123',
            'role': 'teacher'
        }, follow_redirects=True)
        
        assert b'All fields are required' in response.data
    
    def test_registration_invalid_role(self, client):
        """Test registration fails with invalid role."""
        response = client.post('/register', data={
            'username': 'test_user',
            'email': 'test@test.com',
            'password': 'securepass123',
            'role': 'admin'  # Invalid role
        }, follow_redirects=True)
        
        assert b'Invalid role selected' in response.data


@pytest.mark.auth
class TestLogin:
    """Test user login."""
    
    def test_teacher_login_success(self, client, test_data):
        """Test successful teacher login."""
        # Create teacher
        test_data.create_teacher(client, username='login_teacher', password='testpass')
        
        # Login
        response = client.post('/login', data={
            'username': 'login_teacher',
            'password': 'testpass'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Welcome back' in response.data
    
    def test_student_login_success(self, client, test_data):
        """Test successful student login."""
        # Create student
        test_data.create_student(client, username='login_student', password='testpass')
        
        # Login
        response = client.post('/login', data={
            'username': 'login_student',
            'password': 'testpass'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Welcome back' in response.data
    
    def test_login_wrong_password(self, client, test_data):
        """Test login fails with wrong password."""
        # Create user
        test_data.create_teacher(client, username='wrongpass_teacher', password='correctpass')
        
        # Try wrong password
        response = client.post('/login', data={
            'username': 'wrongpass_teacher',
            'password': 'wrongpass'
        }, follow_redirects=True)
        
        assert b'Invalid username or password' in response.data
    
    def test_login_nonexistent_user(self, client):
        """Test login fails for non-existent user."""
        response = client.post('/login', data={
            'username': 'nonexistent_user',
            'password': 'somepass'
        }, follow_redirects=True)
        
        assert b'Invalid username or password' in response.data


@pytest.mark.auth
class TestLogout:
    """Test user logout."""
    
    def test_logout_success(self, client, test_data):
        """Test successful logout."""
        # Create and login user
        test_data.create_teacher(client, username='logout_teacher')
        test_data.login_user(client, 'logout_teacher')
        
        # Logout
        response = client.get('/logout', follow_redirects=True)
        
        assert b'You have been logged out' in response.data
    
    def test_protected_route_requires_login(self, client):
        """Test that protected routes require login."""
        response = client.get('/', follow_redirects=True)
        
        # Should redirect to login
        assert b'Log In' in response.data or b'Please log in' in response.data


@pytest.mark.auth
class TestUserRoles:
    """Test user role functionality."""
    
    def test_teacher_can_create_deck(self, client, test_data, db):
        """Test teacher can create a deck."""
        # Create and login teacher
        test_data.create_teacher(client, username='deck_teacher')
        test_data.login_user(client, 'deck_teacher')
        
        # Create deck
        response = client.post('/create_deck', data={
            'name': 'Teacher Deck'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Teacher Deck' in response.data or b'created' in response.data
    
    def test_student_can_create_deck(self, client, test_data):
        """Test student can create a deck."""
        # Create and login student
        test_data.create_student(client, username='deck_student')
        test_data.login_user(client, 'deck_student')
        
        # Create deck
        response = client.post('/create_deck', data={
            'name': 'Student Deck'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Student Deck' in response.data or b'created' in response.data
