#!/usr/bin/env python3
"""
Bio Age Coach - Setup and Run
"""

import os
import sys
import subprocess

def check_requirements():
    """Check if all required packages are installed."""
    print("Checking requirements...")
    try:
        import streamlit
        import matplotlib
        import numpy
        from dotenv import load_dotenv
        print("Requirements installed successfully!")
        return True
    except ImportError as e:
        print(f"Missing requirement: {e}")
        print("Please install requirements using: pip install -r requirements.txt")
        return False

def main():
    """Main entry point for the Bio Age Coach application."""
    print("="*50)
    print("   Bio Age Coach - Setup and Run")
    print("="*50)
    
    # Get the directory containing this script
    app_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to the app directory
    os.chdir(app_dir)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    print("Starting Bio Age Coach application...")
    print("The app should open in your web browser automatically.")
    print("If not, please visit http://localhost:8501")
    print("Press Ctrl+C to stop the application.")
    
    # Run the Streamlit app
    import streamlit.web.cli as stcli
    
    # Use the correct path to app.py
    app_path = os.path.join(app_dir, "app.py")
    
    if not os.path.exists(app_path):
        print(f"Error: Could not find {app_path}")
        sys.exit(1)
    
    sys.argv = ["streamlit", "run", app_path]
    sys.exit(stcli.main())

if __name__ == "__main__":
    main() 