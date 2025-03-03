"""
Database connector module for the Bio Age Coach application.

This module provides functionality to connect to the SQLite database
and retrieve user health data for the Bio Age Coach.
"""

import os
import sqlite3
import datetime
from typing import Dict, List, Any, Optional, Tuple


class DatabaseConnector:
    """
    Connector for the Bio Age Coach SQLite database.
    
    Handles database connections and data retrieval for the application.
    """
    
    def __init__(self, db_path: str = "data/test_database.db"):
        """
        Initialize the database connector.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found at {db_path}. Please run the data generation script first.")
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Get a connection to the SQLite database.
        
        Returns:
            SQLite database connection
        """
        return sqlite3.connect(self.db_path)
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        Get a list of all users in the database.
        
        Returns:
            List of user dictionaries with id, username, and email
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, username, email FROM users ORDER BY username")
        rows = cursor.fetchall()
        
        users = [dict(row) for row in rows]
        conn.close()
        
        return users
    
    def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific user.
        
        Args:
            user_id: ID of the user to retrieve
            
        Returns:
            Dictionary with user information or None if user not found
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, username, email, date_joined, age, gender, height, weight FROM users WHERE id = ?", 
            (user_id,)
        )
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_daily_health_data(self, user_id: int, limit: int = 30) -> List[Dict[str, Any]]:
        """
        Get daily health data for a user.
        
        Args:
            user_id: ID of the user to retrieve data for
            limit: Maximum number of records to retrieve (newest first)
            
        Returns:
            List of daily health data dictionaries
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT date, active_calories, steps, sleep_hours, daily_score 
            FROM daily_health_data 
            WHERE user_id = ? 
            ORDER BY date DESC 
            LIMIT ?
            """, 
            (user_id, limit)
        )
        rows = cursor.fetchall()
        
        daily_data = [dict(row) for row in rows]
        conn.close()
        
        return daily_data
    
    def get_biomarkers(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get biomarker data for a user.
        
        Args:
            user_id: ID of the user to retrieve data for
            
        Returns:
            List of biomarker data dictionaries
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT date, biomarker_id, value, unit 
            FROM biomarkers 
            WHERE user_id = ? 
            ORDER BY date DESC
            """, 
            (user_id,)
        )
        rows = cursor.fetchall()
        
        biomarkers = [dict(row) for row in rows]
        conn.close()
        
        return biomarkers
    
    def get_functional_tests(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get functional test data for a user.
        
        Args:
            user_id: ID of the user to retrieve data for
            
        Returns:
            List of functional test data dictionaries
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT date, test_id, value, unit 
            FROM functional_tests 
            WHERE user_id = ? 
            ORDER BY date DESC
            """, 
            (user_id,)
        )
        rows = cursor.fetchall()
        
        tests = [dict(row) for row in rows]
        conn.close()
        
        return tests
    
    def get_physical_measurements(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get physical measurement data for a user.
        
        Args:
            user_id: ID of the user to retrieve data for
            
        Returns:
            List of physical measurement data dictionaries
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT date, measurement_id, value, unit 
            FROM physical_measurements 
            WHERE user_id = ? 
            ORDER BY date DESC
            """, 
            (user_id,)
        )
        rows = cursor.fetchall()
        
        measurements = [dict(row) for row in rows]
        conn.close()
        
        return measurements
    
    def get_all_user_health_data(self, user_id: int) -> Dict[str, Any]:
        """
        Get all health data for a user in a structured format.
        
        Args:
            user_id: ID of the user to retrieve data for
            
        Returns:
            Dictionary with all user health data categorized
        """
        user_info = self.get_user_info(user_id)
        daily_data = self.get_daily_health_data(user_id)
        biomarkers = self.get_biomarkers(user_id)
        functional_tests = self.get_functional_tests(user_id)
        physical_measurements = self.get_physical_measurements(user_id)
        
        # Calculate averages from daily data
        avg_calories = sum(d['active_calories'] for d in daily_data) / len(daily_data) if daily_data else 0
        avg_steps = sum(d['steps'] for d in daily_data) / len(daily_data) if daily_data else 0
        avg_sleep = sum(d['sleep_hours'] for d in daily_data) / len(daily_data) if daily_data else 0
        avg_score = sum(d['daily_score'] for d in daily_data) / len(daily_data) if daily_data else 0
        
        return {
            "user_info": user_info,
            "daily_data": {
                "records": daily_data,
                "averages": {
                    "active_calories": round(avg_calories, 1),
                    "steps": round(avg_steps, 0),
                    "sleep_hours": round(avg_sleep, 1),
                    "daily_score": round(avg_score, 1)
                }
            },
            "biomarkers": biomarkers,
            "functional_tests": functional_tests,
            "physical_measurements": physical_measurements
        }


class CoachDataMapper:
    """
    Maps database records to the Bio-Age Coach data model.
    """
    
    @staticmethod
    def map_data_to_coach_format(data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """
        Convert database records to coach's data format.
        
        Args:
            data: The user health data from the database
            
        Returns:
            Data in the format expected by the Bio-Age Coach
        """
        coach_data = {
            "health_data": {},
            "bio_age_tests": {},
            "capabilities": {},
            "biomarkers": {},
            "measurements": {},
            "lab_results": {}
        }
        
        # Map daily health data averages
        if "daily_data" in data and "averages" in data["daily_data"]:
            averages = data["daily_data"]["averages"]
            coach_data["health_data"]["active_calories"] = averages["active_calories"]
            coach_data["health_data"]["steps"] = averages["steps"]
            coach_data["health_data"]["sleep"] = averages["sleep_hours"]
        
        # Map biomarkers
        for biomarker in data.get("biomarkers", []):
            biomarker_id = biomarker["biomarker_id"]
            value = biomarker["value"]
            
            # Categorize biomarkers based on type
            if biomarker_id in ["hba1c", "fasting_glucose", "crp", "hdl", "ldl", "triglycerides"]:
                coach_data["biomarkers"][biomarker_id] = value
            elif biomarker_id in ["vitamin_d"]:
                coach_data["lab_results"][biomarker_id] = value
        
        # Map functional tests - fixing the mapping to UI field names
        for test in data.get("functional_tests", []):
            test_id = test["test_id"]
            value = test["value"]
            
            # Map database test_id to the corresponding UI field names
            if test_id == "push_ups":
                coach_data["bio_age_tests"]["push_ups"] = value
            elif test_id == "grip_strength":
                coach_data["bio_age_tests"]["grip_strength"] = value
            elif test_id == "one_leg_stand":
                coach_data["bio_age_tests"]["one_leg_stand"] = value
            elif test_id == "vo2_max":
                coach_data["bio_age_tests"]["vo2_max"] = value
            elif test_id == "plank":
                coach_data["capabilities"]["plank"] = value
            elif test_id == "sit_and_reach":
                coach_data["capabilities"]["sit_and_reach"] = value
        
        # Map physical measurements
        for measurement in data.get("physical_measurements", []):
            measurement_id = measurement["measurement_id"]
            value = measurement["value"]
            
            if measurement_id in ["body_fat", "waist_circumference", "hip_circumference", "waist_to_hip"]:
                coach_data["measurements"][measurement_id] = value
            elif measurement_id in ["resting_heart_rate", "blood_pressure_systolic", "blood_pressure_diastolic"]:
                coach_data["health_data"][measurement_id] = value
        
        return coach_data


def initialize_coach_with_user_data(coach, db: DatabaseConnector, user_id: int) -> float:
    """
    Initialize the Bio-Age Coach with user data from the database.
    
    Args:
        coach: The Bio-Age Coach instance
        db: Database connector instance
        user_id: ID of the user to load data for
        
    Returns:
        Overall data completeness percentage (0.0-1.0)
    """
    # Get all user health data
    user_data = db.get_all_user_health_data(user_id)
    
    # Map database data to coach format
    coach_data = CoachDataMapper.map_data_to_coach_format(user_data)
    
    # Debug: print the mapped data to see what's going into the coach
    print(f"Mapped coach data: {coach_data}")
    
    # Update coach's user_data
    for category, data in coach_data.items():
        coach.user_data[category].update(data)
    
    # Calculate overall completeness
    completeness = coach.calculate_overall_completeness()
    
    return completeness 