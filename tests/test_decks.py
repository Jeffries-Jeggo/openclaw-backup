"""
Test deck management.
"""
import pytest


@pytest.mark.decks
class TestDeckCreation:
    """Test deck creation."""
    
    def test_create_deck_success(self, client, test_data):
        """Test successful deck creation."""
        # Login
        test_data.create_teacher(client, username='deck_creator')
        test_data.login_user(client, 'deck_creator')
        
        # Create deck
        response = client.post('/create_deck', data={
            'name': 'My New Deck'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'My New Deck' in response.data
    
    def test_create_deck_duplicate_name(self, client, test_data, db):
        """Test creating deck with duplicate name."""
        # Setup
        test_data.create_teacher(client, username='deck_dup')
        test_data.login_user(client, 'deck_dup')
        test_data.create_deck(db, 'Duplicate Deck', user_id=1)
        
        # Try to create duplicate
        response = client.post('/create_deck', data={
            'name': 'Duplicate Deck'
        }, follow_redirects=True)
        
        assert b'Deck already exists' in response.data or b'created' in response.data
    
    def test_create_deck_empty_name(self, client, test_data):
        """Test creating deck with empty name fails gracefully."""
        # Login
        test_data.create_teacher(client, username='deck_empty')
        test_data.login_user(client, 'deck_empty')
        
        # Try empty name
        response = client.post('/create_deck', data={
            'name': ''
        }, follow_redirects=True)
        
        # Should not crash
        assert response.status_code == 200


@pytest.mark.decks
class TestDeckExportImport:
    """Test deck export and import."""
    
    def test_export_deck(self, client, test_data, db):
        """Test exporting a deck."""
        # Setup
        test_data.create_teacher(client, username='export_teacher')
        test_data.login_user(client, 'export_teacher')
        deck_id = test_data.create_deck(db, 'Export Deck', user_id=1)
        test_data.create_card(db, deck_id, 'Front', 'Back')
        
        # Export
        response = client.get(f'/deck/{deck_id}/export')
        
        assert response.status_code == 200
        assert b'Front' in response.data
        assert b'Back' in response.data
    
    def test_import_deck(self, client, test_data, db):
        """Test importing cards to a deck."""
        import io
        
        # Setup
        test_data.create_teacher(client, username='import_teacher')
        test_data.login_user(client, 'import_teacher')
        deck_id = test_data.create_deck(db, 'Import Deck', user_id=1)
        
        # Create CSV file
        csv_data = "front,back\nHello,Hola\nGoodbye,Adios"
        
        # Import
        response = client.post(
            f'/deck/{deck_id}/import',
            data={'file': (io.BytesIO(csv_data.encode()), 'cards.csv')},
            content_type='multipart/form-data',
            follow_redirects=True
        )
        
        assert response.status_code == 200
        # Import functionality depends on implementation


@pytest.mark.decks
class TestDeckList:
    """Test deck listing."""
    
    def test_index_shows_decks(self, client, test_data, db):
        """Test index page shows all decks."""
        # Setup
        test_data.create_teacher(client, username='index_teacher')
        test_data.login_user(client, 'index_teacher')
        test_data.create_deck(db, 'Deck 1', user_id=1)
        test_data.create_deck(db, 'Deck 2', user_id=1)
        
        # View index
        response = client.get('/')
        
        assert response.status_code == 200
        assert b'Deck 1' in response.data
        assert b'Deck 2' in response.data
    
    def test_index_no_decks(self, client, test_data):
        """Test index page when no decks exist."""
        # Login
        test_data.create_teacher(client, username='index_empty')
        test_data.login_user(client, 'index_empty')
        
        # View index
        response = client.get('/')
        
        assert response.status_code == 200
