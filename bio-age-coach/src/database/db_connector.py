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
            "SELECT id, username, email, created_at FROM users WHERE id = ?", 
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
            SELECT date, active_calories, steps, sleep_hours, resting_heart_rate,
                   blood_pressure_systolic, blood_pressure_diastolic, daily_score
            FROM daily_health 
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
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get user info
        user_info = self.get_user_info(user_id)
        
        # Get daily health data
        cursor.execute("""
            SELECT date, active_calories, steps, sleep_hours, resting_heart_rate,
                   blood_pressure_systolic, blood_pressure_diastolic, daily_score
            FROM daily_health 
            WHERE user_id = ? 
            ORDER BY date DESC 
            LIMIT 14
        """, (user_id,))
        daily_data = [dict(row) for row in cursor.fetchall()]
        
        # Get biomarkers
        cursor.execute("""
            SELECT date, hba1c, hdl, ldl, triglycerides, crp, fasting_glucose
            FROM biomarkers 
            WHERE user_id = ? 
            ORDER BY date DESC 
            LIMIT 1
        """, (user_id,))
        biomarker_row = cursor.fetchone()
        biomarkers = dict(biomarker_row) if biomarker_row else {}
        
        # Get bio-age tests
        cursor.execute("""
            SELECT date, push_ups, grip_strength, one_leg_stand, vo2_max
            FROM bio_age_tests 
            WHERE user_id = ? 
            ORDER BY date DESC 
            LIMIT 1
        """, (user_id,))
        test_row = cursor.fetchone()
        bio_age_tests = dict(test_row) if test_row else {}
        
        # Get measurements
        cursor.execute("""
            SELECT date, body_fat, waist_circumference, hip_circumference, waist_to_hip
            FROM measurements 
            WHERE user_id = ? 
            ORDER BY date DESC 
            LIMIT 1
        """, (user_id,))
        measurement_row = cursor.fetchone()
        measurements = dict(measurement_row) if measurement_row else {}
        
        # Get capabilities
        cursor.execute("""
            SELECT date, plank, sit_and_reach
            FROM capabilities 
            WHERE user_id = ? 
            ORDER BY date DESC 
            LIMIT 1
        """, (user_id,))
        capability_row = cursor.fetchone()
        capabilities = dict(capability_row) if capability_row else {}
        
        # Get lab results
        cursor.execute("""
            SELECT date, vitamin_d
            FROM lab_results 
            WHERE user_id = ? 
            ORDER BY date DESC 
            LIMIT 1
        """, (user_id,))
        lab_row = cursor.fetchone()
        lab_results = dict(lab_row) if lab_row else {}
        
        conn.close()
        
        # Calculate averages from daily data if available
        if daily_data:
            avg_calories = sum(d['active_calories'] for d in daily_data) / len(daily_data)
            avg_steps = sum(d['steps'] for d in daily_data) / len(daily_data)
            avg_sleep = sum(d['sleep_hours'] for d in daily_data) / len(daily_data)
            avg_score = sum(d['daily_score'] for d in daily_data) / len(daily_data)
        else:
            avg_calories = avg_steps = avg_sleep = avg_score = 0
        
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
            "bio_age_tests": bio_age_tests,
            "measurements": measurements,
            "capabilities": capabilities,
            "lab_results": lab_results
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
            coach_data["health_data"].update({
                "active_calories": averages["active_calories"],
                "steps": averages["steps"],
                "sleep": averages["sleep_hours"]
            })
            
            # Get the latest daily record for other health metrics
            if data["daily_data"]["records"]:
                latest = data["daily_data"]["records"][0]
                if "resting_heart_rate" in latest:
                    coach_data["health_data"]["resting_heart_rate"] = latest["resting_heart_rate"]
                if "blood_pressure_systolic" in latest and "blood_pressure_diastolic" in latest:
                    coach_data["health_data"]["blood_pressure_systolic"] = latest["blood_pressure_systolic"]
                    coach_data["health_data"]["blood_pressure_diastolic"] = latest["blood_pressure_diastolic"]
        
        # Map biomarkers
        if "biomarkers" in data:
            biomarkers = data["biomarkers"]
            for field in ["hba1c", "hdl", "ldl", "triglycerides", "crp", "fasting_glucose"]:
                if field in biomarkers and biomarkers[field] is not None:
                    coach_data["biomarkers"][field] = biomarkers[field]
        
        # Map bio-age tests
        if "bio_age_tests" in data:
            tests = data["bio_age_tests"]
            for field in ["push_ups", "grip_strength", "one_leg_stand", "vo2_max"]:
                if field in tests and tests[field] is not None:
                    coach_data["bio_age_tests"][field] = tests[field]
        
        # Map measurements
        if "measurements" in data:
            measurements = data["measurements"]
            for field in ["body_fat", "waist_circumference", "hip_circumference", "waist_to_hip"]:
                if field in measurements and measurements[field] is not None:
                    coach_data["measurements"][field] = measurements[field]
        
        # Map capabilities
        if "capabilities" in data:
            capabilities = data["capabilities"]
            for field in ["plank", "sit_and_reach"]:
                if field in capabilities and capabilities[field] is not None:
                    coach_data["capabilities"][field] = capabilities[field]
        
        # Map lab results
        if "lab_results" in data:
            lab_results = data["lab_results"]
            for field in ["vitamin_d"]:
                if field in lab_results and lab_results[field] is not None:
                    coach_data["lab_results"][field] = lab_results[field]
        
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