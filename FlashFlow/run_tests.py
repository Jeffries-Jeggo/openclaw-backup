#!/usr/bin/env python3
"""
Test runner with database backup/restore functionality.
Usage: python run_tests.py [--backup-db path/to/db] [--no-coverage]
"""

import os
import sys
import shutil
import subprocess
import argparse
from datetime import datetime


def backup_database(db_path):
    """Create a backup of the database."""
    if not os.path.exists(db_path):
        print(f"⚠️  Database not found at {db_path}, skipping backup")
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.backup_{timestamp}"
    
    shutil.copy2(db_path, backup_path)
    print(f"✅ Database backed up to: {backup_path}")
    return backup_path


def restore_database(original_path, backup_path):
    """Restore database from backup."""
    if backup_path and os.path.exists(backup_path):
        shutil.copy2(backup_path, original_path)
        print(f"✅ Database restored from: {backup_path}")
        return True
    return False


def run_tests(no_coverage=False):
    """Run pytest with appropriate arguments."""
    cmd = ['python3', '-m', 'pytest']
    
    if not no_coverage:
        cmd.extend(['--cov=app', '--cov-report=term-missing'])
    
    print("\n" + "="*60)
    print("Running tests...")
    print("="*60 + "\n")
    
    result = subprocess.run(cmd)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description='Run FlashFlow tests with database backup/restore')
    parser.add_argument('--backup-db', help='Path to database to backup/restore', default='flashcards.db')
    parser.add_argument('--no-coverage', action='store_true', help='Run tests without coverage')
    parser.add_argument('--test', help='Run specific test file or test')
    
    args = parser.parse_args()
    
    # Store current working directory
    original_cwd = os.getcwd()
    
    try:
        # Change to project directory
        project_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(project_dir)
        
        # Backup database
        backup_path = None
        if args.backup_db and os.path.exists(args.backup_db):
            backup_path = backup_database(args.backup_db)
        
        try:
            # Run tests
            exit_code = run_tests(args.no_coverage)
            
            if exit_code == 0:
                print("\n✅ All tests passed!")
            else:
                print(f"\n❌ Tests failed with exit code: {exit_code}")
            
        finally:
            # Restore database
            if backup_path and os.path.exists(backup_path):
                restore_database(args.backup_db, backup_path)
                # Clean up backup
                os.remove(backup_path)
                print(f"🗑️  Backup removed: {backup_path}")
        
        return exit_code
        
    finally:
        # Restore original directory
        os.chdir(original_cwd)


if __name__ == '__main__':
    sys.exit(main())
