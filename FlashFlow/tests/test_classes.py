"""
Test class management: creation, enrollment, assignment, dashboard, study.
"""
import pytest
import io


def logout(client):
    """Helper to logout current user."""
    client.get('/logout', follow_redirects=True)


@pytest.mark.classes
class TestClassCreation:
    """Test class creation by teachers."""
    
    def test_teacher_can_create_class(self, client, test_data):
        """Test teacher can create a class."""
        test_data.create_teacher(client, username='class_teacher')
        test_data.login_user(client, 'class_teacher')
        
        response = client.post('/classes/new', data={
            'name': 'Biology 101'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Biology 101' in response.data
        assert b'Class code:' in response.data or b'created' in response.data
    
    def test_create_class_empty_name(self, client, test_data):
        """Test creating class with empty name fails."""
        test_data.create_teacher(client, username='class_teacher2')
        test_data.login_user(client, 'class_teacher2')
        
        response = client.post('/classes/new', data={
            'name': ''
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Class name is required' in response.data
    
    def test_student_cannot_create_class(self, client, test_data):
        """Test students cannot create classes."""
        test_data.create_student(client, username='class_student')
        test_data.login_user(client, 'class_student')
        
        response = client.post('/classes/new', data={
            'name': 'Hacked Class'
        }, follow_redirects=True)
        
        assert b'Only teachers can create classes' in response.data
    
    def test_create_class_get_request(self, client, test_data):
        """Test GET request to create class page."""
        test_data.create_teacher(client, username='class_teacher3')
        test_data.login_user(client, 'class_teacher3')
        
        response = client.get('/classes/new')
        
        assert response.status_code == 200


@pytest.mark.classes
class TestClassEnrollment:
    """Test student enrollment in classes."""
    
    def test_student_can_join_class(self, client, test_data, db):
        """Test student can join a class with code."""
        # Create teacher and class
        test_data.create_teacher(client, username='enroll_teacher')
        test_data.login_user(client, 'enroll_teacher')
        class_id = test_data.create_class(db, 'Math Class', 1, class_code='MATH99')
        logout(client)
        
        # Create and login student
        test_data.create_student(client, username='enroll_student')
        test_data.login_user(client, 'enroll_student')
        
        # Join class
        response = client.post('/classes/join', data={
            'class_code': 'MATH99'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Successfully joined' in response.data or b'Math Class' in response.data
    
    def test_join_class_invalid_code(self, client, test_data):
        """Test joining with invalid class code fails."""
        test_data.create_student(client, username='enroll_student2')
        test_data.login_user(client, 'enroll_student2')
        
        response = client.post('/classes/join', data={
            'class_code': 'INVALID'
        }, follow_redirects=True)
        
        assert b'Invalid class code' in response.data
    
    def test_join_class_already_enrolled(self, client, test_data, db):
        """Test joining already enrolled class shows info message."""
        # Create teacher and class
        test_data.create_teacher(client, username='enroll_teacher2')
        test_data.login_user(client, 'enroll_teacher2')
        class_id = test_data.create_class(db, 'Science Class', 1, class_code='SCIENCE')
        logout(client)
        
        # Create and login student
        test_data.create_student(client, username='enroll_student3')
        test_data.login_user(client, 'enroll_student3')
        
        # Join class first time
        client.post('/classes/join', data={'class_code': 'SCIENCE'}, follow_redirects=True)
        
        # Try to join again
        response = client.post('/classes/join', data={
            'class_code': 'SCIENCE'
        }, follow_redirects=True)
        
        assert b'already enrolled' in response.data.lower()
    
    def test_teacher_cannot_join_class(self, client, test_data):
        """Test teachers cannot join classes."""
        test_data.create_teacher(client, username='enroll_teacher3')
        test_data.login_user(client, 'enroll_teacher3')
        
        response = client.post('/classes/join', data={
            'class_code': 'ANYCODE'
        }, follow_redirects=True)
        
        assert b'Teachers cannot join classes' in response.data
    
    def test_join_class_empty_code(self, client, test_data):
        """Test joining with empty code fails."""
        test_data.create_student(client, username='enroll_student4')
        test_data.login_user(client, 'enroll_student4')
        
        response = client.post('/classes/join', data={
            'class_code': ''
        }, follow_redirects=True)
        
        assert b'Class code is required' in response.data
    
    def test_join_class_get_request(self, client, test_data):
        """Test GET request to join class page."""
        test_data.create_student(client, username='enroll_student5')
        test_data.login_user(client, 'enroll_student5')
        
        response = client.get('/classes/join')
        
        assert response.status_code == 200


@pytest.mark.classes
class TestClassListing:
    """Test listing classes for teachers and students."""
    
    def test_teacher_sees_own_classes(self, client, test_data, db):
        """Test teacher sees their created classes."""
        test_data.create_teacher(client, username='list_teacher')
        test_data.login_user(client, 'list_teacher')
        test_data.create_class(db, 'Class A', 1)
        test_data.create_class(db, 'Class B', 1)
        
        response = client.get('/classes')
        
        assert response.status_code == 200
        assert b'Class A' in response.data
        assert b'Class B' in response.data
    
    def test_teacher_no_classes_redirects_to_create(self, client, test_data):
        """Test teacher with no classes is redirected to create page."""
        test_data.create_teacher(client, username='list_teacher2')
        test_data.login_user(client, 'list_teacher2')
        
        response = client.get('/classes', follow_redirects=True)
        
        assert b'No classes yet' in response.data or b'Create Class' in response.data
    
    def test_student_sees_enrolled_classes(self, client, test_data, db):
        """Test student sees enrolled classes."""
        # Create teacher and class
        test_data.create_teacher(client, username='list_teacher3')
        test_data.login_user(client, 'list_teacher3')
        class_id = test_data.create_class(db, 'History Class', 1)
        logout(client)
        
        # Create student and enroll
        test_data.create_student(client, username='list_student')
        test_data.login_user(client, 'list_student')
        test_data.enroll_student(db, class_id, 2)  # student_id=2
        
        response = client.get('/classes')
        
        assert response.status_code == 200
        assert b'History Class' in response.data


@pytest.mark.classes
class TestClassCardAssignment:
    """Test assigning cards to classes."""
    
    def test_teacher_can_assign_cards_to_class(self, client, test_data, db):
        """Test teacher can assign cards to their class."""
        # Setup teacher, deck, cards
        test_data.create_teacher(client, username='assign_teacher')
        test_data.login_user(client, 'assign_teacher')
        deck_id = test_data.create_deck(db, 'Assignment Deck', 1)
        card_id = test_data.create_card(db, deck_id, 'Q1', 'A1', created_by=1)
        class_id = test_data.create_class(db, 'Test Class', 1)
        
        # Assign cards from deck view
        response = client.post(f'/deck/{deck_id}/assign_cards', data={
            'card_ids': [card_id],
            'class_id': class_id
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'assigned' in response.data.lower()
    
    def test_assign_cards_no_selection(self, client, test_data, db):
        """Test assigning with no cards selected shows error."""
        test_data.create_teacher(client, username='assign_teacher2')
        test_data.login_user(client, 'assign_teacher2')
        deck_id = test_data.create_deck(db, 'Assignment Deck 2', 1)
        class_id = test_data.create_class(db, 'Test Class 2', 1)
        
        response = client.post(f'/deck/{deck_id}/assign_cards', data={
            'card_ids': [],
            'class_id': class_id
        }, follow_redirects=True)
        
        assert b'No cards selected' in response.data
    
    def test_assign_cards_no_class_selected(self, client, test_data, db):
        """Test assigning with no class selected shows error."""
        test_data.create_teacher(client, username='assign_teacher3')
        test_data.login_user(client, 'assign_teacher3')
        deck_id = test_data.create_deck(db, 'Assignment Deck 3', 1)
        card_id = test_data.create_card(db, deck_id, 'Q', 'A', created_by=1)
        
        response = client.post(f'/deck/{deck_id}/assign_cards', data={
            'card_ids': [card_id],
            'class_id': ''
        }, follow_redirects=True)
        
        assert b'Please select a class' in response.data
    
    def test_student_cannot_assign_cards(self, client, test_data, db):
        """Test students cannot assign cards."""
        # Create teacher, deck, class
        test_data.create_teacher(client, username='assign_teacher4')
        test_data.login_user(client, 'assign_teacher4')
        deck_id = test_data.create_deck(db, 'Deck', 1)
        card_id = test_data.create_card(db, deck_id, 'Q', 'A', created_by=1)
        class_id = test_data.create_class(db, 'Class', 1)
        logout(client)
        
        # Switch to student
        test_data.create_student(client, username='assign_student')
        test_data.login_user(client, 'assign_student')
        
        response = client.post(f'/deck/{deck_id}/assign_cards', data={
            'card_ids': [card_id],
            'class_id': class_id
        }, follow_redirects=True)
        
        assert b'Only teachers can assign cards' in response.data
    
    def test_assign_to_other_teacher_class_fails(self, client, test_data, db):
        """Test cannot assign cards to another teacher's class."""
        # Create first teacher with class
        test_data.create_teacher(client, username='teacher_a')
        test_data.login_user(client, 'teacher_a')
        deck_id = test_data.create_deck(db, 'Deck A', 1)
        card_id = test_data.create_card(db, deck_id, 'Q', 'A', created_by=1)
        other_class_id = test_data.create_class(db, 'Class A', 1)
        logout(client)
        
        # Create second teacher
        test_data.create_teacher(client, username='teacher_b', email='b@test.com')
        test_data.login_user(client, 'teacher_b')
        
        # Try to assign to first teacher's class
        response = client.post(f'/deck/{deck_id}/assign_cards', data={
            'card_ids': [card_id],
            'class_id': other_class_id
        }, follow_redirects=True)
        
        assert b'Invalid class selected' in response.data
    
    def test_assign_cards_from_class_view(self, client, test_data, db):
        """Test assigning cards from class assignment view."""
        test_data.create_teacher(client, username='assign_teacher5')
        test_data.login_user(client, 'assign_teacher5')
        deck_id = test_data.create_deck(db, 'Deck 5', 1)
        card_id = test_data.create_card(db, deck_id, 'Q5', 'A5', created_by=1)
        class_id = test_data.create_class(db, 'Class 5', 1)
        
        response = client.post(f'/classes/{class_id}/assign', data={
            'card_ids': [card_id]
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'assigned' in response.data.lower()
    
    def test_assign_cards_class_view_no_selection(self, client, test_data, db):
        """Test assigning from class view with no cards selected."""
        test_data.create_teacher(client, username='assign_teacher6')
        test_data.login_user(client, 'assign_teacher6')
        class_id = test_data.create_class(db, 'Class 6', 1)
        
        response = client.post(f'/classes/{class_id}/assign', data={
            'card_ids': []
        }, follow_redirects=True)
        
        assert b'No cards selected' in response.data
    
    def test_assign_cards_class_view_wrong_teacher(self, client, test_data, db):
        """Test cannot access assignment view for another teacher's class."""
        # Create first teacher with class
        test_data.create_teacher(client, username='teacher_c')
        test_data.login_user(client, 'teacher_c')
        class_id = test_data.create_class(db, 'Class C', 1)
        logout(client)
        
        # Create second teacher
        test_data.create_teacher(client, username='teacher_d', email='d@test.com')
        test_data.login_user(client, 'teacher_d')
        
        # Try to access assignment view
        response = client.get(f'/classes/{class_id}/assign', follow_redirects=True)
        
        assert b'Class not found' in response.data or b'access denied' in response.data.lower()
    
    def test_add_card_and_assign_to_class(self, client, test_data, db):
        """Test adding card and assigning to class in one action."""
        test_data.create_teacher(client, username='assign_teacher7')
        test_data.login_user(client, 'assign_teacher7')
        deck_id = test_data.create_deck(db, 'Deck 7', 1)
        class_id = test_data.create_class(db, 'Class 7', 1)
        
        response = client.post(f'/deck/{deck_id}/add_card', data={
            'front': 'New Question',
            'back': 'New Answer',
            'unit_id': '',
            'class_ids': [class_id]
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Card added successfully' in response.data
        assert b'assigned' in response.data.lower()


@pytest.mark.classes
class TestClassDashboard:
    """Test class dashboard for teachers."""
    
    def test_teacher_can_view_dashboard(self, client, test_data, db):
        """Test teacher can view class dashboard."""
        test_data.create_teacher(client, username='dash_teacher')
        test_data.login_user(client, 'dash_teacher')
        class_id = test_data.create_class(db, 'Dashboard Class', 1)
        
        response = client.get(f'/classes/{class_id}/dashboard')
        
        assert response.status_code == 200
        assert b'Dashboard Class' in response.data
    
    def test_student_cannot_view_dashboard(self, client, test_data, db):
        """Test students cannot view class dashboard."""
        # Create teacher and class
        test_data.create_teacher(client, username='dash_teacher2')
        test_data.login_user(client, 'dash_teacher2')
        class_id = test_data.create_class(db, 'Protected Class', 1)
        logout(client)
        
        # Create student
        test_data.create_student(client, username='dash_student')
        test_data.login_user(client, 'dash_student')
        
        response = client.get(f'/classes/{class_id}/dashboard', follow_redirects=True)
        
        assert b'Only teachers can access' in response.data
    
    def test_teacher_cannot_view_other_dashboard(self, client, test_data, db):
        """Test teacher cannot view another teacher's dashboard."""
        # Create first teacher with class
        test_data.create_teacher(client, username='teacher_e')
        test_data.login_user(client, 'teacher_e')
        class_id = test_data.create_class(db, 'Private Class', 1)
        logout(client)
        
        # Create second teacher
        test_data.create_teacher(client, username='teacher_f', email='f@test.com')
        test_data.login_user(client, 'teacher_f')
        
        response = client.get(f'/classes/{class_id}/dashboard', follow_redirects=True)
        
        assert b'Class not found' in response.data or b'access denied' in response.data.lower()
    
    def test_dashboard_with_filters(self, client, test_data, db):
        """Test dashboard with unit and student filters."""
        test_data.create_teacher(client, username='dash_teacher3')
        test_data.login_user(client, 'dash_teacher3')
        class_id = test_data.create_class(db, 'Filtered Class', 1)
        
        # Add unit, student, cards
        unit_id = test_data.create_unit(db, 'Test Unit')
        deck_id = test_data.create_deck(db, 'Filter Deck', 1)
        card_id = test_data.create_card(db, deck_id, 'Q', 'A', unit_id=unit_id, created_by=1)
        
        # Test with filters
        response = client.get(f'/classes/{class_id}/dashboard?unit={unit_id}')
        assert response.status_code == 200


@pytest.mark.classes
class TestClassStudy:
    """Test studying class cards."""
    
    def test_student_can_study_class_cards(self, client, test_data, db):
        """Test student can study cards assigned to class."""
        # Setup teacher, class, deck, card
        test_data.create_teacher(client, username='study_t')
        test_data.login_user(client, 'study_t')
        class_id = test_data.create_class(db, 'Study Class', 1)
        deck_id = test_data.create_deck(db, 'Study Deck', 1)
        card_id = test_data.create_card(db, deck_id, 'Study Q', 'Study A', created_by=1)
        test_data.assign_card_to_class(db, class_id, card_id, 1)
        logout(client)
        
        # Create and enroll student
        test_data.create_student(client, username='study_s')
        test_data.login_user(client, 'study_s')
        test_data.enroll_student(db, class_id, 2)
        
        response = client.get(f'/classes/{class_id}/study', follow_redirects=True)
        
        assert response.status_code == 200
        # Should show card or no cards message
    
    def test_student_not_enrolled_cannot_study(self, client, test_data, db):
        """Test student not enrolled cannot study class cards."""
        # Create teacher and class
        test_data.create_teacher(client, username='study_t2')
        test_data.login_user(client, 'study_t2')
        class_id = test_data.create_class(db, 'Private Study', 1)
        logout(client)
        
        # Create student (not enrolled)
        test_data.create_student(client, username='study_s2')
        test_data.login_user(client, 'study_s2')
        
        response = client.get(f'/classes/{class_id}/study', follow_redirects=True)
        
        # Should show not enrolled or only students can study
        assert b'not enrolled' in response.data.lower() or b'only students can study' in response.data.lower()
    
    def test_teacher_cannot_study_class_cards(self, client, test_data, db):
        """Test teachers cannot study class cards."""
        test_data.create_teacher(client, username='study_t3')
        test_data.login_user(client, 'study_t3')
        class_id = test_data.create_class(db, 'Teacher Study', 1)
        
        response = client.get(f'/classes/{class_id}/study', follow_redirects=True)
        
        assert b'Only students can study' in response.data
    
    def test_rate_class_card(self, client, test_data, db):
        """Test rating a card during class study."""
        # Setup
        test_data.create_teacher(client, username='rate_t')
        test_data.login_user(client, 'rate_t')
        class_id = test_data.create_class(db, 'Rate Class', 1)
        deck_id = test_data.create_deck(db, 'Rate Deck', 1)
        card_id = test_data.create_card(db, deck_id, 'Q', 'A', created_by=1)
        test_data.assign_card_to_class(db, class_id, card_id, 1)
        logout(client)
        
        test_data.create_student(client, username='rate_s')
        test_data.login_user(client, 'rate_s')
        test_data.enroll_student(db, class_id, 2)
        
        response = client.post(f'/classes/{class_id}/rate', data={
            'card_id': card_id,
            'status': 'good'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_rate_class_card_teacher_blocked(self, client, test_data, db):
        """Test teachers cannot rate class cards."""
        test_data.create_teacher(client, username='rate_t2')
        test_data.login_user(client, 'rate_t2')
        class_id = test_data.create_class(db, 'Rate Class 2', 1)
        
        response = client.post(f'/classes/{class_id}/rate', data={
            'card_id': 1,
            'status': 'good'
        }, follow_redirects=True)
        
        assert b'Only students can rate' in response.data
    
    def test_no_cards_due_redirect(self, client, test_data, db):
        """Test redirect when no cards due for class study."""
        # Setup empty class
        test_data.create_teacher(client, username='empty_t')
        test_data.login_user(client, 'empty_t')
        class_id = test_data.create_class(db, 'Empty Class', 1)
        logout(client)
        
        test_data.create_student(client, username='empty_s')
        test_data.login_user(client, 'empty_s')
        test_data.enroll_student(db, class_id, 2)
        
        response = client.get(f'/classes/{class_id}/study', follow_redirects=True)
        
        assert b'No cards due' in response.data or b'classes' in response.data.lower()


@pytest.mark.classes
class TestBulkAssignment:
    """Test bulk card assignment features."""
    
    def test_bulk_assign_multiple_cards(self, client, test_data, db):
        """Test assigning multiple cards at once."""
        test_data.create_teacher(client, username='bulk_t')
        test_data.login_user(client, 'bulk_t')
        deck_id = test_data.create_deck(db, 'Bulk Deck', 1)
        card1 = test_data.create_card(db, deck_id, 'Q1', 'A1', created_by=1)
        card2 = test_data.create_card(db, deck_id, 'Q2', 'A2', created_by=1)
        card3 = test_data.create_card(db, deck_id, 'Q3', 'A3', created_by=1)
        class_id = test_data.create_class(db, 'Bulk Class', 1)
        
        response = client.post(f'/deck/{deck_id}/assign_cards', data={
            'card_ids': [card1, card2, card3],
            'class_id': class_id
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'3 card(s) assigned' in response.data
    
    def test_duplicate_assignment_ignored(self, client, test_data, db):
        """Test assigning same card twice is handled gracefully."""
        test_data.create_teacher(client, username='dup_t')
        test_data.login_user(client, 'dup_t')
        deck_id = test_data.create_deck(db, 'Dup Deck', 1)
        card_id = test_data.create_card(db, deck_id, 'Q', 'A', created_by=1)
        class_id = test_data.create_class(db, 'Dup Class', 1)
        
        # Assign once
        client.post(f'/deck/{deck_id}/assign_cards', data={
            'card_ids': [card_id],
            'class_id': class_id
        }, follow_redirects=True)
        
        # Assign again
        response = client.post(f'/deck/{deck_id}/assign_cards', data={
            'card_ids': [card_id],
            'class_id': class_id
        }, follow_redirects=True)
        
        # Should not crash
        assert response.status_code == 200
