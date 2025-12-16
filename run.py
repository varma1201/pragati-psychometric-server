"""
Pragati Psychometric Server - Entry Point
Run with: python run.py or python3 run.py
"""

import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import the Flask app
from app.server import create_app

if __name__ == "__main__":
    # Create the Flask application
    app = create_app()
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 7000))
    debug = os.getenv("FLASK_ENV") == "development"
    
    print("\n" + "="*70)
    print("🚀 Starting Pragati Psychometric Server")
    print("="*70)
    print(f"📍 Host: {host}")
    print(f"📍 Port: {port}")
    print(f"📍 Debug Mode: {debug}")
    print(f"📍 URL: http://{host}:{port}")
    print(f"📍 Health Check: http://{host}:{port}/health")
    print("="*70 + "\n")
    
    # Run the application
    app.run(host=host, port=port, debug=debug)
