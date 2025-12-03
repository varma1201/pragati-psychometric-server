"""
Pragati Psychometric Server

Flask microservice for psychometric assessments and evaluations
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Import extensions
from .extensions import setup_logging, init_app_config
from .psychometric_endpoints import register_psychometric_endpoints
from .database_manager import get_database_manager


# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logging("pragati-psychometric")


def create_app() -> Flask:
    """Create and configure Flask application"""
    
    app = Flask(__name__)
    
    # Initialize configuration
    init_app_config(app)
    
    # Enable CORS
    CORS(app)
    
    logger.info("Flask app initialized")
    
    # Initialize database manager
    try:
        db_manager = get_database_manager()
        logger.info("Database manager connected")
    except Exception as e:
        logger.error(f"Database connection warning: {e}")
        db_manager = None
    
    # Health check endpoint
    @app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint"""
        return jsonify({
            "status": "ok",
            "service": "pragati-psychometric-server",
            "version": "1.0.0"
        }), 200
    
    # Register psychometric endpoints
    register_psychometric_endpoints(app)
    logger.info("Psychometric endpoints registered")
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "Endpoint not found",
            "message": "Please check the API documentation"
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "error": "Internal server error",
            "message": "Something went wrong on our end"
        }), 500
    
    logger.info("Pragati Psychometric Server initialized successfully")
    
    return app


if __name__ == "__main__":
    app = create_app()
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 7000))
    debug = os.getenv("FLASK_ENV") == "development"
    
    logger.info(f"Starting server on {host}:{port} (debug={debug})")
    
    app.run(host=host, port=port, debug=debug)
