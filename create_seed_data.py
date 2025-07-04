#!/usr/bin/env python3
"""
Script to create seed data for the MES system
"""
import os
import sys

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.seed_data import seed_all

def main():
    """Create and seed the database"""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created")
        
        # Seed with default data
        seed_all()
        print("Seed data creation completed")

if __name__ == '__main__':
    main() 