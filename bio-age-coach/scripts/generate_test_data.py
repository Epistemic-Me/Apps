"""
Generate test data for the Bio Age Coach application.

This script creates a SQLite database with test users and their health data.
It generates random but realistic data for testing the database integration
features of the Bio Age Coach.
"""

import os
import json
import sqlite3
import random
import datetime
import math
from typing import Dict, List, Any, Tuple

# Configuration
NUM_USERS = 10
NUM_DAYS = 30
DB_PATH = "data/test_database.db"
SCHEMA_PATH = "data/schema.sql"

# Ensure the data directory exists
os.makedirs("data", exist_ok=True)

def calculate_daily_score(active_calories: float, steps: int, sleep: float) -> int:
    """
    Calculate a daily health score based on the three core metrics.
    
    Args:
        active_calories: Active calories burned
        steps: Steps taken
        sleep: Hours of sleep
        
    Returns:
        Score from 0-100
    """
    cal_score = min(active_calories / 350 * 10, 10)
    steps_score = min(steps / 3500 * 10, 10)
    sleep_score = min(sleep / 7 * 80, 80)
    
    return round(cal_score + steps_score + sleep_score)

def create_database() -> None:
    """Create a new SQLite database and apply the schema."""
    # Delete existing database if it exists
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    # Create the schema if it doesn't exist yet
    if not os.path.exists(SCHEMA_PATH):
        create_schema()
    
    # Create the database and apply the schema
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, 'r') as f:
        schema_sql = f.read()
        conn.executescript(schema_sql)
    conn.commit()
    conn.close()
    
    print(f"Created database at {DB_PATH}")

def create_schema() -> None:
    """Create the database schema SQL file."""
    schema = """
    -- User table to store basic user information
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT NOT NULL,
        date_joined TEXT NOT NULL,
        age INTEGER,
        gender TEXT,
        height REAL,  -- in cm
        weight REAL   -- in kg
    );
    
    -- Daily health data for core metrics
    CREATE TABLE daily_health_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        active_calories REAL,
        steps INTEGER,
        sleep_hours REAL,
        daily_score INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    
    -- Biomarkers table for lab results and biomarker data
    CREATE TABLE biomarkers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        biomarker_id TEXT NOT NULL,  -- e.g., "hba1c", "crp", etc.
        value REAL NOT NULL,
        unit TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    
    -- Physical measurements
    CREATE TABLE physical_measurements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        measurement_id TEXT NOT NULL,  -- e.g., "body_fat", "waist_circumference", etc.
        value REAL NOT NULL,
        unit TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    
    -- Functional tests for physical capabilities
    CREATE TABLE functional_tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        test_id TEXT NOT NULL,  -- e.g., "push_ups", "grip_strength", etc.
        value REAL NOT NULL,
        unit TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """
    
    with open(SCHEMA_PATH, 'w') as f:
        f.write(schema)
    
    print(f"Created schema at {SCHEMA_PATH}")

def generate_user_data() -> List[Dict[str, Any]]:
    """
    Generate random user data and insert it into the database.
    
    Returns:
        List of user data dictionaries
    """
    users = []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Common first and last names for generating usernames
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth"]
    last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor"]
    
    for i in range(1, NUM_USERS + 1):
        # Generate user data
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        username = f"{first_name.lower()}{last_name.lower()}{random.randint(1, 99)}"
        email = f"{username}@example.com"
        date_joined = (datetime.datetime.now() - datetime.timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d")
        age = random.randint(25, 65)
        gender = random.choice(["Male", "Female"])
        height = round(random.uniform(150, 195), 1)
        weight = round(random.uniform(50, 100), 1)
        
        # Insert into database
        cursor.execute("""
            INSERT INTO users (username, email, date_joined, age, gender, height, weight)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (username, email, date_joined, age, gender, height, weight))
        
        user_id = cursor.lastrowid
        
        # Add to our list
        users.append({
            "id": user_id,
            "username": username,
            "email": email,
            "date_joined": date_joined,
            "age": age,
            "gender": gender,
            "height": height,
            "weight": weight
        })
    
    conn.commit()
    conn.close()
    
    print(f"Generated {len(users)} users")
    return users

def generate_daily_health_data(users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate daily health metrics for each user.
    
    Args:
        users: List of user data dictionaries
        
    Returns:
        List of daily health data dictionaries
    """
    daily_data = []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for user in users:
        user_id = user["id"]
        
        # Generate base metrics with random variation around a typical value
        base_active_calories = random.randint(250, 450)
        base_steps = random.randint(3000, 7000)
        base_sleep = round(random.uniform(6.0, 8.0), 1)
        
        # Generate data for each day
        end_date = datetime.datetime.now()
        for day in range(NUM_DAYS):
            # Calculate date
            date = (end_date - datetime.timedelta(days=day)).strftime("%Y-%m-%d")
            
            # Add some randomness to the base values
            day_multiplier = 0.7 + (random.random() * 0.6)  # 0.7 to 1.3
            active_calories = round(base_active_calories * day_multiplier)
            
            # Steps are higher on weekdays, lower on weekends
            weekday = datetime.datetime.strptime(date, "%Y-%m-%d").weekday()
            weekend_factor = 0.8 if weekday >= 5 else 1.0  # Weekend = 0.8x
            steps = int(base_steps * day_multiplier * weekend_factor)
            
            # Sleep varies less
            sleep_hours = round(base_sleep + (random.random() - 0.5), 1)
            
            # Calculate the daily score
            daily_score = calculate_daily_score(active_calories, steps, sleep_hours)
            
            # Insert into database
            cursor.execute("""
                INSERT INTO daily_health_data (user_id, date, active_calories, steps, sleep_hours, daily_score)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, date, active_calories, steps, sleep_hours, daily_score))
            
            # Add to our list
            daily_data.append({
                "user_id": user_id,
                "date": date,
                "active_calories": active_calories,
                "steps": steps,
                "sleep_hours": sleep_hours,
                "daily_score": daily_score
            })
    
    conn.commit()
    conn.close()
    
    print(f"Generated {len(daily_data)} daily health records")
    return daily_data

def generate_biomarker_data(users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate biomarker data for each user.
    
    Args:
        users: List of user data dictionaries
        
    Returns:
        List of biomarker data dictionaries
    """
    biomarker_data = []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Define biomarkers with normal ranges and units
    biomarkers = [
        {"id": "hba1c", "min": 4.0, "max": 6.0, "unit": "%"},
        {"id": "fasting_glucose", "min": 70, "max": 100, "unit": "mg/dL"},
        {"id": "crp", "min": 0.0, "max": 3.0, "unit": "mg/L"},
        {"id": "hdl", "min": 40, "max": 60, "unit": "mg/dL"},
        {"id": "ldl", "min": 70, "max": 130, "unit": "mg/dL"},
        {"id": "triglycerides", "min": 50, "max": 150, "unit": "mg/dL"},
        {"id": "vitamin_d", "min": 30, "max": 50, "unit": "ng/mL"}
    ]
    
    for user in users:
        user_id = user["id"]
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Determine how many biomarkers to generate (different for each user)
        completeness = random.random()  # 0.0 to 1.0
        num_biomarkers = math.ceil(completeness * len(biomarkers))
        selected_biomarkers = random.sample(biomarkers, num_biomarkers)
        
        for biomarker in selected_biomarkers:
            # Generate a value within or slightly outside the normal range
            in_range = random.random() > 0.3  # 70% chance of being in normal range
            
            if in_range:
                value = round(random.uniform(biomarker["min"], biomarker["max"]), 1)
            else:
                # Generate a value slightly outside the range
                higher = random.random() > 0.5
                if higher:
                    value = round(biomarker["max"] + random.uniform(0.1, biomarker["max"] * 0.2), 1)
                else:
                    value = round(biomarker["min"] - random.uniform(0.1, biomarker["min"] * 0.2), 1)
                    value = max(0, value)  # Ensure no negative values
            
            # Insert into database
            cursor.execute("""
                INSERT INTO biomarkers (user_id, date, biomarker_id, value, unit)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, date, biomarker["id"], value, biomarker["unit"]))
            
            # Add to our list
            biomarker_data.append({
                "user_id": user_id,
                "date": date,
                "biomarker_id": biomarker["id"],
                "value": value,
                "unit": biomarker["unit"]
            })
    
    conn.commit()
    conn.close()
    
    print(f"Generated {len(biomarker_data)} biomarker records")
    return biomarker_data

def generate_physical_measurement_data(users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate physical measurement data for each user.
    
    Args:
        users: List of user data dictionaries
        
    Returns:
        List of physical measurement data dictionaries
    """
    measurement_data = []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Define physical measurements with normal ranges and units
    measurements = [
        {"id": "body_fat", "min": 10, "max": 25, "unit": "%"},
        {"id": "waist_circumference", "min": 70, "max": 90, "unit": "cm"},
        {"id": "hip_circumference", "min": 90, "max": 110, "unit": "cm"},
        {"id": "waist_to_hip", "min": 0.7, "max": 0.9, "unit": "ratio"},
        {"id": "resting_heart_rate", "min": 55, "max": 75, "unit": "bpm"},
        {"id": "blood_pressure_systolic", "min": 100, "max": 130, "unit": "mmHg"},
        {"id": "blood_pressure_diastolic", "min": 60, "max": 85, "unit": "mmHg"}
    ]
    
    for user in users:
        user_id = user["id"]
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Determine how many measurements to generate (different for each user)
        completeness = random.random()  # 0.0 to 1.0
        num_measurements = math.ceil(completeness * len(measurements))
        selected_measurements = random.sample(measurements, num_measurements)
        
        for measurement in selected_measurements:
            # Generate a value within or slightly outside the normal range
            in_range = random.random() > 0.3  # 70% chance of being in normal range
            
            if in_range:
                value = round(random.uniform(measurement["min"], measurement["max"]), 1)
            else:
                # Generate a value slightly outside the range
                higher = random.random() > 0.5
                if higher:
                    value = round(measurement["max"] + random.uniform(0.1, measurement["max"] * 0.2), 1)
                else:
                    value = round(measurement["min"] - random.uniform(0.1, measurement["min"] * 0.2), 1)
                    value = max(0, value)  # Ensure no negative values
            
            # Insert into database
            cursor.execute("""
                INSERT INTO physical_measurements (user_id, date, measurement_id, value, unit)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, date, measurement["id"], value, measurement["unit"]))
            
            # Add to our list
            measurement_data.append({
                "user_id": user_id,
                "date": date,
                "measurement_id": measurement["id"],
                "value": value,
                "unit": measurement["unit"]
            })
    
    conn.commit()
    conn.close()
    
    print(f"Generated {len(measurement_data)} physical measurement records")
    return measurement_data

def generate_functional_test_data(users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate functional test data for each user.
    
    Args:
        users: List of user data dictionaries
        
    Returns:
        List of functional test data dictionaries
    """
    test_data = []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Define functional tests with ranges and units
    tests = [
        {"id": "push_ups", "min": 10, "max": 30, "unit": "reps"},
        {"id": "grip_strength", "min": 80, "max": 130, "unit": "kg"},
        {"id": "sit_and_reach", "min": 0, "max": 20, "unit": "cm"},
        {"id": "one_leg_stand", "min": 10, "max": 60, "unit": "seconds"},
        {"id": "vo2_max", "min": 30, "max": 50, "unit": "ml/kg/min"},
        {"id": "plank", "min": 30, "max": 120, "unit": "seconds"}
    ]
    
    for user in users:
        user_id = user["id"]
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Determine how many tests to generate (different for each user)
        completeness = random.random()  # 0.0 to 1.0
        num_tests = math.ceil(completeness * len(tests))
        selected_tests = random.sample(tests, num_tests)
        
        for test in selected_tests:
            # Generate a value within or slightly outside the normal range
            in_range = random.random() > 0.3  # 70% chance of being in normal range
            
            if in_range:
                value = round(random.uniform(test["min"], test["max"]), 1)
            else:
                # Generate a value slightly outside the range
                higher = random.random() > 0.5
                if higher:
                    value = round(test["max"] + random.uniform(0.1, test["max"] * 0.2), 1)
                else:
                    value = round(test["min"] - random.uniform(0.1, test["min"] * 0.2), 1)
                    value = max(0, value)  # Ensure no negative values
            
            # Insert into database
            cursor.execute("""
                INSERT INTO functional_tests (user_id, date, test_id, value, unit)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, date, test["id"], value, test["unit"]))
            
            # Add to our list
            test_data.append({
                "user_id": user_id,
                "date": date,
                "test_id": test["id"],
                "value": value,
                "unit": test["unit"]
            })
    
    conn.commit()
    conn.close()
    
    print(f"Generated {len(test_data)} functional test records")
    return test_data

def save_data_json(data: Dict[str, Any]) -> None:
    """
    Save all generated data to a JSON file for reference.
    
    Args:
        data: Dictionary of all generated data
    """
    with open("data/test_data.json", 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Saved all data to data/test_data.json")

def main():
    """Main function to orchestrate test data generation."""
    print("Generating test data for Bio Age Coach...")
    
    # Create the database and schema
    create_database()
    
    # Generate user data
    users = generate_user_data()
    
    # Generate daily health data
    daily_data = generate_daily_health_data(users)
    
    # Generate biomarker data
    biomarker_data = generate_biomarker_data(users)
    
    # Generate physical measurement data
    measurement_data = generate_physical_measurement_data(users)
    
    # Generate functional test data
    test_data = generate_functional_test_data(users)
    
    # Save all data to a JSON file
    all_data = {
        "users": users,
        "daily_health_data": daily_data,
        "biomarkers": biomarker_data,
        "measurements": measurement_data,
        "functional_tests": test_data
    }
    save_data_json(all_data)
    
    print("Test data generation complete!")

if __name__ == "__main__":
    main() 