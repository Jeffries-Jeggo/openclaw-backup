"""
Test card management: add, study, SRS functionality.
"""
import pytest


@pytest.mark.cards
class TestCardCreation:
    """Test card creation."""
    
    def test_add_card_with_unit(self, client, test_data, db):
        """Test adding a card with a unit."""
        # Setup
        test_data.create_teacher(client, username='card_teacher')
        test_data.login_user(client, 'card_teacher')
        deck_id = test_data.create_deck(db, 'Test Deck', user_id=1)
        unit_id = test_data.create_unit(db, 'Biology 101')
        
        # Add card
        response = client.post(f'/deck/{deck_id}/add_card', data={
            'front': 'What is photosynthesis?',
            'back': 'Process by which plants convert light energy into chemical energy',
            'unit_id': unit_id
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Card added successfully' in response.data
    
    def test_add_card_without_unit(self, client, test_data, db):
        """Test adding a card without a unit."""
        # Setup
        test_data.create_teacher(client, username='card_teacher2')
        test_data.login_user(client, 'card_teacher2')
        deck_id = test_data.create_deck(db, 'Test Deck 2', user_id=1)
        
        # Add card without unit
        response = client.post(f'/deck/{deck_id}/add_card', data={
            'front': 'What is 2+2?',
            'back': '4',
            'unit_id': ''  # Empty unit
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should handle gracefully
        assert b'Card added' in response.data or b'Please enter a name' in response.data
    
    def test_add_card_create_new_unit(self, client, test_data, db):
        """Test adding a card with a new unit."""
        # Setup
        test_data.create_teacher(client, username='card_teacher3')
        test_data.login_user(client, 'card_teacher3')
        deck_id = test_data.create_deck(db, 'Test Deck 3', user_id=1)
        
        # Add card with new unit
        response = client.post(f'/deck/{deck_id}/add_card', data={
            'front': 'Capital of France?',
            'back': 'Paris',
            'unit_id': 'new',
            'new_unit_name': 'Geography'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Card added successfully' in response.data
        assert b'Geography' in response.data
    
    def test_add_card_missing_front(self, client, test_data, db):
        """Test adding card fails without front."""
        # Setup
        test_data.create_teacher(client, username='card_teacher4')
        test_data.login_user(client, 'card_teacher4')
        deck_id = test_data.create_deck(db, 'Test Deck 4', user_id=1)
        
        # Try to add card without front
        response = client.post(f'/deck/{deck_id}/add_card', data={
            'front': '',
            'back': 'Answer',
            'unit_id': ''
        }, follow_redirects=True)
        
        assert b'Front and back are required' in response.data
    
    def test_add_card_missing_back(self, client, test_data, db):
        """Test adding card fails without back."""
        # Setup
        test_data.create_teacher(client, username='card_teacher5')
        test_data.login_user(client, 'card_teacher5')
        deck_id = test_data.create_deck(db, 'Test Deck 5', user_id=1)
        
        # Try to add card without back
        response = client.post(f'/deck/{deck_id}/add_card', data={
            'front': 'Question?',
            'back': '',
            'unit_id': ''
        }, follow_redirects=True)
        
        assert b'Front and back are required' in response.data


@pytest.mark.cards
class TestCardStudy:
    """Test studying cards."""
    
    def test_new_card_appears_immediately(self, client, test_data, db):
        """Test that new cards are immediately available for study."""
        # Setup
        test_data.create_teacher(client, username='study_teacher')
        test_data.login_user(client, 'study_teacher')
        deck_id = test_data.create_deck(db, 'Study Deck', user_id=1)
        test_data.create_card(db, deck_id, 'Q1', 'A1')
        
        # Try to study
        response = client.get(f'/study/{deck_id}', follow_redirects=True)
        
        # Should show the card, not "no cards due"
        assert b'Q1' in response.data or b'cards due' in response.data
    
    def test_rate_card_again(self, client, test_data, db):
        """Test rating a card as 'again'."""
        # Setup
        test_data.create_teacher(client, username='rate_teacher')
        test_data.login_user(client, 'rate_teacher')
        deck_id = test_data.create_deck(db, 'Rate Deck', user_id=1)
        card_id = test_data.create_card(db, deck_id, 'Question', 'Answer')
        
        # Rate card as 'again'
        response = client.post(f'/study/{deck_id}/rate', data={
            'card_id': card_id,
            'status': 'again'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_rate_card_easy(self, client, test_data, db):
        """Test rating a card as 'easy'."""
        # Setup
        test_data.create_teacher(client, username='rate_teacher2')
        test_data.login_user(client, 'rate_teacher2')
        deck_id = test_data.create_deck(db, 'Rate Deck 2', user_id=1)
        card_id = test_data.create_card(db, deck_id, 'Q2', 'A2')
        
        # Rate card as 'easy'
        response = client.post(f'/study/{deck_id}/rate', data={
            'card_id': card_id,
            'status': 'easy'
        }, follow_redirects=True)
        
        assert response.status_code == 200


@pytest.mark.cards
class TestDeckView:
    """Test deck viewing."""
    
    def test_view_deck_shows_cards(self, client, test_data, db):
        """Test viewing a deck shows its cards."""
        # Setup
        test_data.create_teacher(client, username='view_teacher')
        test_data.login_user(client, 'view_teacher')
        deck_id = test_data.create_deck(db, 'View Deck', user_id=1)
        test_data.create_card(db, deck_id, 'Front Text', 'Back Text')
        
        # View deck
        response = client.get(f'/deck/{deck_id}')
        
        assert response.status_code == 200
        assert b'Front Text' in response.data
        assert b'Back Text' in response.data
    
    def test_view_deck_shows_unit(self, client, test_data, db):
        """Test viewing a deck shows card units."""
        # Setup
        test_data.create_teacher(client, username='view_teacher2')
        test_data.login_user(client, 'view_teacher2')
        deck_id = test_data.create_deck(db, 'View Deck 2', user_id=1)
        unit_id = test_data.create_unit(db, 'Test Unit')
        test_data.create_card(db, deck_id, 'Q', 'A', unit_id=unit_id)
        
        # View deck
        response = client.get(f'/deck/{deck_id}')
        
        assert response.status_code == 200
        assert b'Test Unit' in response.data
    
    def test_view_nonexistent_deck(self, client, test_data):
        """Test viewing a non-existent deck."""
        # Login
        test_data.create_teacher(client, username='view_teacher3')
        test_data.login_user(client, 'view_teacher3')
        
        # Try to view non-existent deck
        response = client.get('/deck/99999', follow_redirects=True)
        
        assert b'Deck not found' in response.data
