-- User Profile Schema for Bio Age Coach

-- Core user profile table
CREATE TABLE user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    health_data_summary TEXT,  -- JSON summary of latest health data observations
    target_habits TEXT,        -- JSON array of target habits
    current_habits TEXT,       -- JSON array of current habits
    beliefs TEXT,             -- JSON object of health beliefs
    change_readiness TEXT     -- JSON object tracking readiness for different changes
);

-- Health data observations from uploaded data
CREATE TABLE health_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    observation_type TEXT NOT NULL,  -- e.g., 'sleep', 'exercise', 'nutrition'
    observation_data TEXT NOT NULL,  -- JSON of the ObservationContext
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
);

-- Coaching sessions
CREATE TABLE coaching_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    session_type TEXT NOT NULL,  -- e.g., 'initial_assessment', 'follow_up', 'plan_update'
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    session_data TEXT,  -- JSON of full session data
    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
);

-- Session questions and responses
CREATE TABLE session_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    interaction_type TEXT NOT NULL,  -- e.g., 'habit_assessment', 'belief_exploration', 'plan_discussion'
    question TEXT NOT NULL,
    response TEXT,
    relevancy_score FLOAT,
    personalization_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES coaching_sessions(id)
);

-- Action plans
CREATE TABLE action_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    session_id INTEGER NOT NULL,
    plan_type TEXT NOT NULL,  -- e.g., 'sleep_improvement', 'exercise_routine'
    current_state TEXT,       -- JSON of current state assessment
    target_state TEXT,        -- JSON of target state
    actions TEXT,             -- JSON array of recommended actions
    user_selected_actions TEXT, -- JSON array of actions user agreed to
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id),
    FOREIGN KEY (session_id) REFERENCES coaching_sessions(id)
);

-- Indexes for performance
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_health_observations_user_id ON health_observations(user_id);
CREATE INDEX idx_coaching_sessions_user_id ON coaching_sessions(user_id);
CREATE INDEX idx_action_plans_user_id ON action_plans(user_id);
CREATE INDEX idx_session_interactions_session_id ON session_interactions(session_id); 