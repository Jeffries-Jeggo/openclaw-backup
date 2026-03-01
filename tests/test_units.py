"""
Test unit/topic management.
"""
import pytest


@pytest.mark.units
class TestUnitCreation:
    """Test unit creation."""
    
    def test_create_unit_with_card(self, client, test_data, db):
        """Test creating a new unit when adding a card."""
        # Setup
        test_data.create_teacher(client, username='unit_teacher')
        test_data.login_user(client, 'unit_teacher')
        deck_id = test_data.create_deck(db, 'Unit Deck', user_id=1)
        
        # Add card with new unit
        response = client.post(f'/deck/{deck_id}/add_card', data={
            'front': 'Question?',
            'back': 'Answer!',
            'unit_id': 'new',
            'new_unit_name': 'History 101'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Card added successfully' in response.data
        assert b'History 101' in response.data
    
    def test_use_existing_unit(self, client, test_data, db):
        """Test using an existing unit."""
        # Setup
        test_data.create_teacher(client, username='unit_teacher2')
        test_data.login_user(client, 'unit_teacher2')
        deck_id = test_data.create_deck(db, 'Unit Deck 2', user_id=1)
        unit_id = test_data.create_unit(db, 'Chemistry')
        
        # Add card with existing unit
        response = client.post(f'/deck/{deck_id}/add_card', data={
            'front': 'What is H2O?',
            'back': 'Water',
            'unit_id': unit_id
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Card added successfully' in response.data
    
    def test_add_card_page_shows_units(self, client, test_data, db):
        """Test add card page shows available units."""
        # Setup
        test_data.create_teacher(client, username='unit_teacher3')
        test_data.login_user(client, 'unit_teacher3')
        deck_id = test_data.create_deck(db, 'Unit Deck 3', user_id=1)
        test_data.create_unit(db, 'Physics')
        test_data.create_unit(db, 'Biology')
        
        # View add card page
        response = client.get(f'/deck/{deck_id}/add_card')
        
        assert response.status_code == 200
        assert b'Physics' in response.data
        assert b'Biology' in response.data
        assert b'Add New Unit' in response.data
    
    def test_create_duplicate_unit(self, client, test_data, db):
        """Test creating a unit that already exists."""
        # Setup
        test_data.create_teacher(client, username='unit_teacher4')
        test_data.login_user(client, 'unit_teacher4')
        deck_id = test_data.create_deck(db, 'Unit Deck 4', user_id=1)
        test_data.create_unit(db, 'Existing Unit')
        
        # Try to create duplicate
        response = client.post(f'/deck/{deck_id}/add_card', data={
            'front': 'Q?',
            'back': 'A!',
            'unit_id': 'new',
            'new_unit_name': 'Existing Unit'
        }, follow_redirects=True)
        
        # Should use existing unit
        assert response.status_code == 200
        assert b'Using existing unit' in response.data or b'Card added' in response.data
