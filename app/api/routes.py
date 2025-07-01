from app.api import bp
from flask import jsonify

@bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'MES Authentication'}), 200

@bp.route('/protected', methods=['GET'])
def protected_endpoint():
    """Protected endpoint for testing authentication"""
    return jsonify({'message': 'This is a protected endpoint'}), 200 