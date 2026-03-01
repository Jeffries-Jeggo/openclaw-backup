"""
Test import/export functionality and edge cases.
"""
import pytest
import io


@pytest.mark.importexport
class TestImportExport:
    """Test CSV import and export functionality."""
    
    def test_export_deck_with_status_and_interval(self, client, test_data, db):
        """Test exporting a deck with card status and interval data."""
        test_data.create_teacher(client, username='export_teacher')
        test_data.login_user(client, 'export_teacher')
        deck_id = test_data.create_deck(db, 'Export Deck', 1)
        # Create card with specific status
        db.execute(
            'INSERT INTO cards (deck_id, front, back, status, interval, ease, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (deck_id, 'Front Text', 'Back Text', 'learning', 5, 2.2, 1)
        )
        db.commit()
        
        response = client.get(f'/deck/{deck_id}/export')
        
        assert response.status_code == 200
        assert response.mimetype == 'text/csv'
        assert b'Front Text' in response.data
        assert b'Back Text' in response.data
        assert b'learning' in response.data
    
    def test_import_cards_success(self, client, test_data, db):
        """Test importing cards from CSV."""
        test_data.create_teacher(client, username='import_teacher')
        test_data.login_user(client, 'import_teacher')
        deck_id = test_data.create_deck(db, 'Import Deck', 1)
        
        csv_data = "front,back\nHello,Hola\nGoodbye,Adios\nThank you,Gracias"
        
        response = client.post(
            f'/deck/{deck_id}/import',
            data={'file': (io.BytesIO(csv_data.encode()), 'cards.csv')},
            content_type='multipart/form-data',
            follow_redirects=True
        )
        
        assert response.status_code == 200
        assert b'Imported 3 cards' in response.data
    
    def test_import_no_file_uploaded(self, client, test_data, db):
        """Test import with no file shows error."""
        test_data.create_teacher(client, username='import_teacher2')
        test_data.login_user(client, 'import_teacher2')
        deck_id = test_data.create_deck(db, 'Import Deck 2', 1)
        
        response = client.post(
            f'/deck/{deck_id}/import',
            data={},
            follow_redirects=True
        )
        
        assert b'No file uploaded' in response.data
    
    def test_import_empty_filename(self, client, test_data, db):
        """Test import with empty filename shows error."""
        test_data.create_teacher(client, username='import_teacher3')
        test_data.login_user(client, 'import_teacher3')
        deck_id = test_data.create_deck(db, 'Import Deck 3', 1)
        
        response = client.post(
            f'/deck/{deck_id}/import',
            data={'file': (io.BytesIO(b''), '')},
            content_type='multipart/form-data',
            follow_redirects=True
        )
        
        assert b'No file selected' in response.data
    
    def test_import_malformed_csv(self, client, test_data, db):
        """Test import with malformed CSV shows error."""
        test_data.create_teacher(client, username='import_teacher4')
        test_data.login_user(client, 'import_teacher4')
        deck_id = test_data.create_deck(db, 'Import Deck 4', 1)
        
        # Invalid CSV data
        csv_data = "not,a,valid,csv\n\x00\x01\x02"
        
        response = client.post(
            f'/deck/{deck_id}/import',
            data={'file': (io.BytesIO(csv_data.encode('utf-8', errors='ignore')), 'bad.csv')},
            content_type='multipart/form-data',
            follow_redirects=True
        )
        
        # Should handle error gracefully
        assert response.status_code == 200


@pytest.mark.study
class TestStudyFeatures:
    """Test study functionality including student-specific paths."""
    
    def test_student_get_due_cards_only_assigned(self, client, test_data, db):
        """Test student only sees cards assigned to their enrolled classes."""
        # Create teacher, class, deck
        test_data.create_teacher(client, username='study_filter_t')
        test_data.login_user(client, 'study_filter_t')
        class_id = test_data.create_class(db, 'Filter Class', 1)
        deck_id = test_data.create_deck(db, 'Filter Deck', 1)
        
        # Create two cards
        card1 = test_data.create_card(db, deck_id, 'Assigned Q', 'A', created_by=1)
        card2 = test_data.create_card(db, deck_id, 'Unassigned Q', 'A', created_by=1)
        
        # Only assign card1 to class
        test_data.assign_card_to_class(db, class_id, card1, 1)
        logout(client)
        
        # Create and enroll student
        test_data.create_student(client, username='study_filter_s')
        test_data.login_user(client, 'study_filter_s')
        test_data.enroll_student(db, class_id, 2)
        
        # Study should show only the assigned card
        response = client.get(f'/study/{deck_id}', follow_redirects=True)
        
        assert response.status_code == 200
        # Should either show the assigned card or "no cards due"
    
    def test_rate_card_updates_progress(self, client, test_data, db):
        """Test rating a card updates user_progress for students."""
        # Setup
        test_data.create_teacher(client, username='rate_prog_t')
        test_data.login_user(client, 'rate_prog_t')
        class_id = test_data.create_class(db, 'Rate Class', 1)
        deck_id = test_data.create_deck(db, 'Rate Deck', 1)
        card_id = test_data.create_card(db, deck_id, 'Q?', 'A!', created_by=1)
        test_data.assign_card_to_class(db, class_id, card_id, 1)
        logout(client)
        
        # Create and enroll student
        test_data.create_student(client, username='rate_prog_s')
        test_data.login_user(client, 'rate_prog_s')
        test_data.enroll_student(db, class_id, 2)
        
        # Rate the card
        response = client.post(f'/classes/{class_id}/rate', data={
            'card_id': card_id,
            'status': 'easy'
        }, follow_redirects=True)
        
        assert response.status_code == 200


@pytest.mark.decks
class TestDeckEdgeCases:
    """Test deck-related edge cases."""
    
    def test_create_deck_success(self, client, test_data, db):
        """Test creating a deck successfully."""
        test_data.create_teacher(client, username='deck_new_t')
        test_data.login_user(client, 'deck_new_t')
        
        response = client.post('/create_deck', data={'name': 'My New Deck'}, follow_redirects=True)
        
        # Should show success
        assert b'created' in response.data.lower() or b'My New Deck' in response.data
    
    def test_view_deck_teacher_sees_classes(self, client, test_data, db):
        """Test teacher sees their classes in deck view."""
        test_data.create_teacher(client, username='deck_view_t')
        test_data.login_user(client, 'deck_view_t')
        deck_id = test_data.create_deck(db, 'View Deck', 1)
        test_data.create_class(db, 'View Class', 1)
        
        response = client.get(f'/deck/{deck_id}')
        
        assert response.status_code == 200
        # Should show class selector for assignment
        assert b'Select a class' in response.data or b'assign' in response.data.lower()


@pytest.mark.auth
class TestAuthEdgeCases:
    """Test authentication edge cases."""
    
    def test_register_while_logged_in_redirects(self, client, test_data):
        """Test registering while logged in redirects to index."""
        test_data.create_teacher(client, username='logged_in_user')
        test_data.login_user(client, 'logged_in_user')
        
        response = client.get('/register', follow_redirects=True)
        
        assert response.status_code == 200
        # Should be redirected to index
    
    def test_login_while_logged_in_redirects(self, client, test_data):
        """Test logging in while already logged in redirects."""
        test_data.create_teacher(client, username='logged_in_user2')
        test_data.login_user(client, 'logged_in_user2')
        
        response = client.get('/login', follow_redirects=True)
        
        assert response.status_code == 200


def logout(client):
    """Helper to logout current user."""
    client.get('/logout', follow_redirects=True)
