"""Database migrations for Bio Age Coach."""

import os
import sqlite3
from typing import List, Dict, Any
from datetime import datetime
import json

class Migration:
    """Base class for database migrations."""
    
    def __init__(self, version: int, description: str):
        self.version = version
        self.description = description
    
    def up(self, conn: sqlite3.Connection) -> None:
        """Apply the migration."""
        raise NotImplementedError
    
    def down(self, conn: sqlite3.Connection) -> None:
        """Revert the migration."""
        raise NotImplementedError

class CreateUserProfileTables(Migration):
    """Initial migration to create user profile tables."""
    
    def __init__(self):
        super().__init__(1, "Create user profile tables")
    
    def up(self, conn: sqlite3.Connection) -> None:
        """Create initial tables."""
        conn.executescript("""
            -- Version tracking
            CREATE TABLE IF NOT EXISTS schema_versions (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Core user profile table
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY,
                user_id TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                health_data_summary TEXT,
                target_habits TEXT,
                current_habits TEXT,
                beliefs TEXT,
                change_readiness TEXT
            );
            
            -- Health data observations
            CREATE TABLE IF NOT EXISTS health_observations (
                id INTEGER PRIMARY KEY,
                user_id TEXT NOT NULL,
                observation_type TEXT NOT NULL,
                observation_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
            );
            
            -- Coaching sessions
            CREATE TABLE IF NOT EXISTS coaching_sessions (
                id INTEGER PRIMARY KEY,
                user_id TEXT NOT NULL,
                session_type TEXT NOT NULL,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                session_data TEXT,
                FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
            );
            
            -- Session interactions
            CREATE TABLE IF NOT EXISTS session_interactions (
                id INTEGER PRIMARY KEY,
                session_id INTEGER NOT NULL,
                interaction_type TEXT NOT NULL,
                question TEXT NOT NULL,
                response TEXT,
                relevancy_score REAL,
                personalization_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES coaching_sessions(id)
            );
            
            -- Action plans
            CREATE TABLE IF NOT EXISTS action_plans (
                id INTEGER PRIMARY KEY,
                user_id TEXT NOT NULL,
                session_id INTEGER NOT NULL,
                plan_type TEXT NOT NULL,
                current_state TEXT,
                target_state TEXT,
                actions TEXT,
                user_selected_actions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_profiles(user_id),
                FOREIGN KEY (session_id) REFERENCES coaching_sessions(id)
            );
            
            -- Indexes
            CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
            CREATE INDEX IF NOT EXISTS idx_health_observations_user_id ON health_observations(user_id);
            CREATE INDEX IF NOT EXISTS idx_coaching_sessions_user_id ON coaching_sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_action_plans_user_id ON action_plans(user_id);
            CREATE INDEX IF NOT EXISTS idx_session_interactions_session_id ON session_interactions(session_id);
        """)
    
    def down(self, conn: sqlite3.Connection) -> None:
        """Drop all tables."""
        conn.executescript("""
            DROP INDEX IF EXISTS idx_session_interactions_session_id;
            DROP INDEX IF EXISTS idx_action_plans_user_id;
            DROP INDEX IF EXISTS idx_coaching_sessions_user_id;
            DROP INDEX IF EXISTS idx_health_observations_user_id;
            DROP INDEX IF EXISTS idx_user_profiles_user_id;
            DROP TABLE IF EXISTS action_plans;
            DROP TABLE IF EXISTS session_interactions;
            DROP TABLE IF EXISTS coaching_sessions;
            DROP TABLE IF EXISTS health_observations;
            DROP TABLE IF EXISTS user_profiles;
            DROP TABLE IF EXISTS schema_versions;
        """)

class DatabaseManager:
    """Manages database connections and migrations."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.migrations: List[Migration] = [
            CreateUserProfileTables()
        ]
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        return sqlite3.connect(self.db_path)
    
    def get_current_version(self, conn: sqlite3.Connection) -> int:
        """Get the current database version."""
        try:
            cursor = conn.execute("SELECT MAX(version) FROM schema_versions")
            version = cursor.fetchone()[0]
            return version if version is not None else 0
        except sqlite3.OperationalError:
            return 0
    
    def migrate(self, target_version: int = None) -> None:
        """Run migrations up to target_version."""
        if target_version is None:
            target_version = len(self.migrations)
        
        conn = self.get_connection()
        try:
            current_version = self.get_current_version(conn)
            
            if current_version < target_version:
                # Migrate up
                for migration in self.migrations[current_version:target_version]:
                    print(f"Applying migration {migration.version}: {migration.description}")
                    migration.up(conn)
                    conn.execute(
                        "INSERT INTO schema_versions (version) VALUES (?)",
                        (migration.version,)
                    )
                    conn.commit()
            elif current_version > target_version:
                # Migrate down
                for migration in reversed(self.migrations[target_version:current_version]):
                    print(f"Reverting migration {migration.version}: {migration.description}")
                    migration.down(conn)
                    conn.execute(
                        "DELETE FROM schema_versions WHERE version = ?",
                        (migration.version,)
                    )
                    conn.commit()
        finally:
            conn.close()
    
    def reset_database(self) -> None:
        """Reset the database to empty state."""
        conn = self.get_connection()
        try:
            # Revert all migrations
            self.migrate(0)
            # Apply all migrations
            self.migrate()
        finally:
            conn.close()

def init_database(db_path: str = None) -> DatabaseManager:
    """Initialize the database."""
    if db_path is None:
        db_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "bio_age_coach.db")
    
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    db_manager = DatabaseManager(db_path)
    db_manager.migrate()
    
    return db_manager 