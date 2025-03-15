"""
Database initialization script for Bio Age Coach.
Creates and populates the database with sample data if it doesn't exist.
"""

import os
import sqlite3
from datetime import datetime, timedelta
import random

def init_database(db_path="data/test_database.db"):
    """Initialize the database with tables and sample data."""
    # Ensure data directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Create database and tables
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create tables
    c.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            chronological_age INTEGER,
            biological_sex TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS daily_health (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            date DATE,
            active_calories REAL,
            steps INTEGER,
            sleep_hours REAL,
            resting_heart_rate INTEGER,
            blood_pressure_systolic INTEGER,
            blood_pressure_diastolic INTEGER,
            daily_score REAL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );

        CREATE TABLE IF NOT EXISTS biomarkers (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            date DATE,
            hba1c REAL,
            hdl REAL,
            ldl REAL,
            triglycerides REAL,
            crp REAL,
            fasting_glucose REAL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );

        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            date DATE,
            body_fat REAL,
            waist_circumference REAL,
            hip_circumference REAL,
            waist_to_hip REAL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );

        CREATE TABLE IF NOT EXISTS bio_age_tests (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            date DATE,
            push_ups INTEGER,
            grip_strength REAL,
            one_leg_stand REAL,
            vo2_max REAL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );

        CREATE TABLE IF NOT EXISTS capabilities (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            date DATE,
            plank REAL,
            sit_and_reach REAL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );

        CREATE TABLE IF NOT EXISTS lab_results (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            date DATE,
            vitamin_d REAL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
    ''')
    
    # Check if we already have sample data
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        # Insert sample users with age and sex
        sample_users = [
            (1, "John Smith", "john@example.com", 35, "male"),
            (2, "Emma Davis", "emma@example.com", 55, "female"),
            (3, "Michael Chen", "michael@example.com", 45, "male")
        ]
        c.executemany("INSERT INTO users (id, username, email, chronological_age, biological_sex) VALUES (?, ?, ?, ?, ?)", sample_users)
        
        # Generate sample daily health data for last 14 days
        today = datetime.now().date()
        for user_id in [1, 2, 3]:
            for days_ago in range(14):
                date = today - timedelta(days=days_ago)
                # Generate realistic but varying health data
                daily_data = (
                    user_id,
                    date,
                    random.uniform(300, 500),  # active_calories
                    random.randint(3000, 8000),  # steps
                    random.uniform(6, 8),  # sleep_hours
                    random.randint(55, 75),  # resting_heart_rate
                    random.randint(110, 130),  # blood_pressure_systolic
                    random.randint(70, 85),  # blood_pressure_diastolic
                    random.uniform(70, 95)  # daily_score
                )
                c.execute("""
                    INSERT INTO daily_health 
                    (user_id, date, active_calories, steps, sleep_hours, 
                     resting_heart_rate, blood_pressure_systolic, 
                     blood_pressure_diastolic, daily_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, daily_data)
        
        # Insert sample biomarker data
        sample_biomarkers = [
            (1, today, 5.2, 58.4, 81.0, 135.0, 0.3, 72.4),
            (2, today, 5.4, 66.4, 92.0, 128.0, 0.4, 75.0),
            (3, today, 5.1, 62.0, 88.0, 142.0, 0.2, 70.0)
        ]
        c.executemany("""
            INSERT INTO biomarkers 
            (user_id, date, hba1c, hdl, ldl, triglycerides, crp, fasting_glucose)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_biomarkers)
        
        # Insert sample measurements
        sample_measurements = [
            (1, today, 29.4, 77.8, 96.0, 0.81),
            (2, today, 8.0, 57.3, 102.4, 0.7),
            (3, today, 18.5, 82.0, 98.0, 0.84)
        ]
        c.executemany("""
            INSERT INTO measurements 
            (user_id, date, body_fat, waist_circumference, hip_circumference, waist_to_hip)
            VALUES (?, ?, ?, ?, ?, ?)
        """, sample_measurements)
        
        # Insert sample bio-age tests
        sample_tests = [
            (1, today, 25, 95.0, 45.0, 35.0),
            (2, today, 34, 85.0, 38.0, 32.0),
            (3, today, 30, 90.0, 42.0, 38.0)
        ]
        c.executemany("""
            INSERT INTO bio_age_tests 
            (user_id, date, push_ups, grip_strength, one_leg_stand, vo2_max)
            VALUES (?, ?, ?, ?, ?, ?)
        """, sample_tests)
        
        # Insert sample capabilities
        sample_capabilities = [
            (1, today, 26.5, None),
            (2, today, 84.7, 0.1),
            (3, today, 45.0, 0.2)
        ]
        c.executemany("""
            INSERT INTO capabilities 
            (user_id, date, plank, sit_and_reach)
            VALUES (?, ?, ?, ?)
        """, sample_capabilities)
        
        # Insert sample lab results
        sample_lab_results = [
            (1, today, None),
            (2, today, 26.0),
            (3, today, 32.0)
        ]
        c.executemany("""
            INSERT INTO lab_results 
            (user_id, date, vitamin_d)
            VALUES (?, ?, ?)
        """, sample_lab_results)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_database() 