import os
from dotenv import load_dotenv
from app import create_app, db
from app.models import User, Role, Permission, AuditLog
from app.seed_data import seed_all

# Load environment variables from .env file
load_dotenv()

def create_tables():
    """Create database tables"""
    db.create_all()
    print("Database tables created successfully")

def init_database():
    """Initialize database with default data"""
    create_tables()
    seed_all()

if __name__ == '__main__':
    app = create_app('development')
    
    with app.app_context():
        # Initialize database if needed
        if not os.path.exists('migrations'):
            print("Initializing database for the first time...")
            init_database()
        
        # Run the application
        app.run(host='0.0.0.0', port=5000, debug=True) 