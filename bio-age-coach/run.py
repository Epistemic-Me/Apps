#!/usr/bin/env python3
"""
Bio Age Coach - Setup and Run
"""

import os
import sys
import subprocess
from src.database.init_db import init_database

def check_requirements():
    """Check if all required packages are installed."""
    try:
        import streamlit
        import matplotlib
        import numpy
        import openai
        import python_dotenv
        return True
    except ImportError as e:
        print(f"Missing requirement: {e.name}")
        return False

def main():
    """Main entry point for the Bio Age Coach application."""
    print("=" * 50)
    print("   Bio Age Coach - Setup and Run")
    print("=" * 50)
    
    # Check requirements
    print("Checking requirements...")
    if not check_requirements():
        print("Installing requirements...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("Requirements installed successfully!")
    
    # Initialize database with sample data if it doesn't exist
    db_path = "data/test_database.db"
    if not os.path.exists(db_path):
        print("Initializing database with sample data...")
        init_database(db_path)
        print("Database initialized successfully!")
    
    # Start the Streamlit app
    print("Starting Bio Age Coach application...")
    print("The app should open in your web browser automatically.")
    print("If not, please visit http://localhost:8501")
    print("Press Ctrl+C to stop the application.")
    
    # Use streamlit.web.cli to run the app
    import streamlit.web.cli as stcli
    sys.argv = ["streamlit", "run", "app.py"]
    sys.exit(stcli.main())

if __name__ == "__main__":
    main() 