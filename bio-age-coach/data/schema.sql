
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
    