"""
Setup script to copy sample data files to the test_health_data directory.

This ensures that the sample data files are available for testing with the HealthServer.
"""

import os
import shutil
import sys

def setup_test_data():
    """Copy sample data files to test_health_data directory."""
    # Get the path to the data directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(os.path.dirname(script_dir))  # Apps/bio-age-coach
    data_dir = os.path.join(project_dir, "data")
    test_data_dir = os.path.join(data_dir, "test_health_data")
    
    print(f"Script directory: {script_dir}")
    print(f"Project directory: {project_dir}")
    print(f"Data directory: {data_dir}")
    print(f"Test data directory: {test_data_dir}")
    
    # Create test_health_data directory if it doesn't exist
    if not os.path.exists(test_data_dir):
        print(f"Creating directory: {test_data_dir}")
        os.makedirs(test_data_dir)
    
    # Sample data files to copy
    sample_files = [
        "sample_sleep_data.csv",
        "sample_exercise_data.csv",
        "sample_nutrition_data.csv",
        "sample_biometric_data.csv"
    ]
    
    # Copy each sample file to test_health_data directory
    for file_name in sample_files:
        source_path = os.path.join(data_dir, file_name)
        dest_path = os.path.join(test_data_dir, file_name)
        
        if not os.path.exists(source_path):
            print(f"Warning: Source file not found: {source_path}")
            continue
        
        print(f"Copying {file_name} to {test_data_dir}")
        shutil.copy2(source_path, dest_path)
        print(f"Successfully copied {file_name}")
    
    print("\nTest data setup complete!")
    print(f"Sample files copied to: {test_data_dir}")

if __name__ == "__main__":
    setup_test_data() 