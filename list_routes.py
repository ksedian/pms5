#!/usr/bin/env python3
"""
Script to list all Flask routes
"""
import os
import sys

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

def main():
    """List all Flask routes"""
    app = create_app()
    
    print("Available Flask routes:")
    print("-" * 50)
    
    with app.app_context():
        for rule in app.url_map.iter_rules():
            print(f"{rule.methods} {rule.rule}")

if __name__ == '__main__':
    main() 