#!/usr/bin/env python3
"""
Bio Age Coach - Run Script

This script helps to launch the Bio Age Coach application
and handle database initialization.
"""

import os
import sys
import subprocess
import time


def check_database():
    """Check if the database exists and create it if not."""
    db_path = "data/test_database.db"
    if not os.path.exists(db_path):
        print("Database not found. Generating test data...")
        try:
            # Ensure data directory exists
            os.makedirs("data", exist_ok=True)
            
            # Run the test data generation script
            result = subprocess.run(
                ["python", "scripts/generate_test_data.py"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print("Error generating test data:")
                print(result.stderr)
                return False
            
            print("Test data generated successfully!")
            return True
        except Exception as e:
            print(f"Error creating database: {e}")
            return False
    return True


def install_requirements():
    """Check and install required packages."""
    try:
        print("Checking requirements...")
        # Run pip install -r requirements.txt
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("Error installing requirements:")
            print(result.stderr)
            return False
        
        print("Requirements installed successfully!")
        return True
    except Exception as e:
        print(f"Error installing requirements: {e}")
        return False


def run_app():
    """Run the Streamlit app."""
    try:
        print("Starting Bio Age Coach application...")
        print("The app should open in your web browser automatically.")
        print("If not, please visit http://localhost:8501")
        print("\nPress Ctrl+C to stop the application.")
        
        # Run the Streamlit app
        subprocess.run(["streamlit", "run", "app.py"])
        return True
    except KeyboardInterrupt:
        print("\nApplication stopped.")
        return True
    except Exception as e:
        print(f"Error running application: {e}")
        return False


def main():
    """Main function to run the Bio Age Coach."""
    print("=" * 50)
    print("   Bio Age Coach - Setup and Run")
    print("=" * 50)
    
    # Check if requirements.txt exists
    if not os.path.exists("requirements.txt"):
        print("Error: requirements.txt not found.")
        print("Please make sure you're running this script from the Bio Age Coach directory.")
        return False
    
    # Install requirements
    if not install_requirements():
        print("Failed to install requirements. Please check your Python setup.")
        return False
    
    # Check/create database
    if not check_database():
        print("Failed to create test database. Please check your permissions.")
        return False
    
    # Run the app
    return run_app()


if __name__ == "__main__":
    main() 