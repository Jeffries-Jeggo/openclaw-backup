"""
Test database migrations.
"""
import pytest
import sqlite3


import app as app_module

@pytest.mark.slow
class TestDatabaseMigrations:
    """Test database migration functionality."""
    
    def test_units_table_created(self, flask_app):
        """Test that units table is created."""
        with flask_app.app_context():
            conn = app_module.get_db_connection()
            
            # Try to query units table
            result = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='units'")
            assert result.fetchone() is not None
            
            conn.close()
    
    def test_cards_has_unit_id(self, flask_app):
        """Test that cards table has unit_id column."""
        with flask_app.app_context():
            conn = app_module.get_db_connection()
            
            # Try to query with unit_id
            result = conn.execute("PRAGMA table_info(cards)")
            columns = [row[1] for row in result.fetchall()]
            
            assert 'unit_id' in columns
            
            conn.close()
