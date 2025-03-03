"""
Bio Age Coach - Streamlit App
"""

import os
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from src.chatbot.coach import BioAgeCoach
from src.database.db_connector import DatabaseConnector, initialize_coach_with_user_data
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize session state
if "coach" not in st.session_state:
    st.session_state.coach = BioAgeCoach()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_category" not in st.session_state:
    st.session_state.current_category = "biomarkers"

if "selected_user_id" not in st.session_state:
    st.session_state.selected_user_id = None

if "user_data_loaded" not in st.session_state:
    st.session_state.user_data_loaded = False

if "db_initialized" not in st.session_state:
    try:
        # Check if the database exists
        db_path = "data/test_database.db"
        if os.path.exists(db_path):
            st.session_state.db = DatabaseConnector(db_path)
            st.session_state.db_initialized = True
        else:
            st.session_state.db_initialized = False
    except Exception as e:
        st.session_state.db_initialized = False
        st.error(f"Error initializing database: {e}")

def draw_completeness_chart(completeness_data):
    """Draw a radar chart showing data completeness across categories."""
    categories = list(completeness_data.keys())
    values = list(completeness_data.values())
    
    # Number of categories
    N = len(categories)
    
    # Create angles for each category
    angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
    
    # Make the plot circular by appending the first value to the end
    values.append(values[0])
    angles.append(angles[0])
    categories.append(categories[0])
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
    
    # Draw one axis per variable and add labels
    plt.xticks(angles[:-1], categories[:-1], color='grey', size=8)
    
    # Draw the chart
    ax.plot(angles, values, linewidth=2, linestyle='solid')
    ax.fill(angles, values, alpha=0.25)
    
    # Set y-axis limits
    ax.set_ylim(0, 1)
    
    # Add percentage labels at specific radii
    ax.set_rticks([0.25, 0.5, 0.75, 1.0])  # Set radii where we want labels
    ax.set_yticklabels(['25%', '50%', '75%', '100%'], fontsize=7)  # Set labels
    
    # Add a title
    plt.title('Health Data Completeness', size=11)
    
    return fig

def load_user_data(user_id):
    """Load user data from the database into the coach."""
    if not st.session_state.db_initialized:
        st.error("Database is not initialized")
        return False
    
    try:
        # Reset the coach to clear any existing data
        st.session_state.coach.reset()
        
        # Initialize coach with user data from database
        completeness = initialize_coach_with_user_data(st.session_state.coach, st.session_state.db, user_id)
        
        # Get user info
        user_info = st.session_state.db.get_user_info(user_id)
        
        if user_info and completeness > 0:
            # Create data summary
            data_summary = st.session_state.coach.get_existing_data_summary()
            initial_assessment = st.session_state.coach.get_initial_biological_age_assessment()
            
            # Set up the welcome message based on data completeness
            welcome_message = f"👋 Hello {user_info['username']}! I've loaded your health data profile, which is currently {int(completeness*100)}% complete."
            
            if completeness < 0.2:
                welcome_message += "\n\nYou're just getting started! Let's collect some fundamental measurements to better understand your biological age factors."
            elif completeness < 0.5:
                welcome_message += "\n\nYou have a good foundation of health data. Let's fill in some key metrics to get a clearer picture of your biological age."
            elif completeness < 0.8:
                welcome_message += "\n\nYour health profile is quite comprehensive. We can now provide a meaningful assessment of your biological age factors."
            else:
                welcome_message += "\n\nYou have an excellent health profile with comprehensive data. This allows for a detailed analysis of your biological age and optimization opportunities."
            
            # Add the welcome message to the chat
            st.session_state.messages = []
            st.session_state.messages.append({"role": "assistant", "content": welcome_message})
            
            return True
        else:
            st.error("No data found for selected user")
            return False
    except Exception as e:
        st.error(f"Error loading user data: {e}")
        return False

def get_daily_health_summary(user_id):
    """Get a summary of the user's daily health metrics from the database."""
    if not st.session_state.db_initialized:
        return None
    
    try:
        # Get the daily health data for the user
        daily_data = st.session_state.db.get_daily_health_data(user_id, limit=14)  # Last 14 days
        
        if not daily_data:
            return None
        
        # Calculate averages
        avg_calories = sum(d['active_calories'] for d in daily_data) / len(daily_data)
        avg_steps = sum(d['steps'] for d in daily_data) / len(daily_data)
        avg_sleep = sum(d['sleep_hours'] for d in daily_data) / len(daily_data)
        avg_score = sum(d['daily_score'] for d in daily_data) / len(daily_data)
        
        # Create a summary
        summary = {
            "avg_calories": round(avg_calories, 1),
            "avg_steps": round(avg_steps, 0),
            "avg_sleep": round(avg_sleep, 1),
            "avg_score": round(avg_score, 1),
            "days": len(daily_data),
            "latest_date": daily_data[0]['date'] if daily_data else None
        }
        
        return summary
    except Exception as e:
        print(f"Error getting daily health summary: {e}")
        return None

def display_health_data_profile(coach):
    """
    Display the user's health data profile in the sidebar as context for the chat.
    
    Args:
        coach: The Bio-Age Coach instance with loaded user data
    """
    if not coach.user_data:
        return
    
    with st.sidebar.expander("📊 YOUR HEALTH PROFILE", expanded=True):
        # Create tabs for different categories
        tabs = st.tabs(["Health", "Bio Tests", "Biomarkers", "Measurements", "Other"])
        
        # Get all expected fields from the biomarkers categories
        expected_fields = {}
        for category_key, category_data in coach.biomarkers.get("categories", {}).items():
            expected_fields[category_key] = [item["id"] for item in category_data.get("items", [])]
        
        # Daily Health Data tab
        with tabs[0]:
            st.subheader("Daily Health")
            # Calculate completeness for this category
            health_fields = expected_fields.get("health_data", [])
            available_fields = set(coach.user_data["health_data"].keys())
            if health_fields:
                completeness = int(len(available_fields.intersection(health_fields)) / len(health_fields) * 100)
                st.caption(f"Completeness: {completeness}%")
            
            if coach.user_data["health_data"]:
                st.markdown("#### Available Data")
                for key, value in coach.user_data["health_data"].items():
                    # Format the display name
                    display_name = " ".join(word.capitalize() for word in key.split('_'))
                    
                    # Add units where appropriate
                    units = ""
                    if "calories" in key:
                        units = " kcal"
                    elif key == "sleep":
                        units = " hrs"
                    elif "heart_rate" in key:
                        units = " bpm"
                    elif "pressure" in key:
                        units = " mmHg"
                    
                    # Display the value with a green indicator
                    st.markdown(f"✅ **{display_name}:** {value}{units}")
            
            # Show missing fields
            missing_fields = [field for field in health_fields if field not in available_fields]
            if missing_fields:
                st.markdown("#### Missing Data")
                for field in missing_fields:
                    # Get display name from biomarkers definition
                    display_name = field
                    for item in coach.biomarkers.get("categories", {}).get("health_data", {}).get("items", []):
                        if item["id"] == field:
                            display_name = item["name"]
                            break
                    
                    # Display as missing with a red indicator
                    st.markdown(f"❌ **{display_name}**")
            
            if not coach.user_data["health_data"] and not missing_fields:
                st.caption("No daily health data available")
        
        # Bio-Age Tests tab
        with tabs[1]:
            st.subheader("Bio-Age Tests")
            # Calculate completeness for this category
            bio_test_fields = expected_fields.get("bio_age_tests", [])
            available_fields = set(coach.user_data["bio_age_tests"].keys())
            if bio_test_fields:
                completeness = int(len(available_fields.intersection(bio_test_fields)) / len(bio_test_fields) * 100)
                st.caption(f"Completeness: {completeness}%")
            
            if coach.user_data["bio_age_tests"]:
                st.markdown("#### Available Tests")
                for key, value in coach.user_data["bio_age_tests"].items():
                    # Format the display name
                    display_name = " ".join(word.capitalize() for word in key.split('_'))
                    
                    # Add units where appropriate
                    units = ""
                    if key == "push_ups":
                        units = " reps"
                    elif key == "grip_strength":
                        units = " kg"
                    elif key == "one_leg_stand":
                        units = " sec"
                    elif key == "vo2_max":
                        units = " ml/kg/min"
                    
                    # Display the value with a green indicator
                    st.markdown(f"✅ **{display_name}:** {value}{units}")
            
            # Show missing fields
            missing_fields = [field for field in bio_test_fields if field not in available_fields]
            if missing_fields:
                st.markdown("#### Missing Tests")
                for field in missing_fields:
                    # Get display name from biomarkers definition
                    display_name = field
                    for item in coach.biomarkers.get("categories", {}).get("bio_age_tests", {}).get("items", []):
                        if item["id"] == field:
                            display_name = item["name"]
                            break
                    
                    # Display as missing with a red indicator
                    st.markdown(f"❌ **{display_name}**")
            
            if not coach.user_data["bio_age_tests"] and not missing_fields:
                st.caption("No bio-age test data available")
        
        # Biomarkers tab
        with tabs[2]:
            st.subheader("Biomarkers")
            # Calculate completeness for this category
            biomarker_fields = expected_fields.get("biomarkers", [])
            available_fields = set(coach.user_data["biomarkers"].keys())
            if biomarker_fields:
                completeness = int(len(available_fields.intersection(biomarker_fields)) / len(biomarker_fields) * 100)
                st.caption(f"Completeness: {completeness}%")
            
            if coach.user_data["biomarkers"]:
                st.markdown("#### Available Biomarkers")
                for key, value in coach.user_data["biomarkers"].items():
                    # Format the display name
                    display_name = key.upper() if len(key) <= 3 else " ".join(word.capitalize() for word in key.split('_'))
                    
                    # Add units where appropriate
                    units = ""
                    if key in ["hdl", "ldl", "triglycerides"]:
                        units = " mg/dL"
                    elif key == "hba1c":
                        units = "%"
                    elif key == "crp":
                        units = " mg/L"
                    elif key == "fasting_glucose":
                        units = " mg/dL"
                    
                    # Display the value with a green indicator
                    st.markdown(f"✅ **{display_name}:** {value}{units}")
            
            # Show missing fields
            missing_fields = [field for field in biomarker_fields if field not in available_fields]
            if missing_fields:
                st.markdown("#### Missing Biomarkers")
                for field in missing_fields:
                    # Get display name from biomarkers definition
                    display_name = field.upper() if len(field) <= 3 else " ".join(word.capitalize() for word in field.split('_'))
                    for item in coach.biomarkers.get("categories", {}).get("biomarkers", {}).get("items", []):
                        if item["id"] == field:
                            display_name = item["name"]
                            break
                    
                    # Display as missing with a red indicator
                    st.markdown(f"❌ **{display_name}**")
            
            if not coach.user_data["biomarkers"] and not missing_fields:
                st.caption("No biomarker data available")
        
        # Measurements tab
        with tabs[3]:
            st.subheader("Measurements")
            # Calculate completeness for this category
            measurement_fields = expected_fields.get("measurements", [])
            available_fields = set(coach.user_data["measurements"].keys())
            if measurement_fields:
                completeness = int(len(available_fields.intersection(measurement_fields)) / len(measurement_fields) * 100)
                st.caption(f"Completeness: {completeness}%")
            
            if coach.user_data["measurements"]:
                st.markdown("#### Available Measurements")
                for key, value in coach.user_data["measurements"].items():
                    # Format the display name
                    display_name = " ".join(word.capitalize() for word in key.split('_'))
                    
                    # Add units where appropriate
                    units = ""
                    if key == "body_fat":
                        units = "%"
                    elif key in ["waist_circumference", "hip_circumference"]:
                        units = " cm"
                    elif key == "waist_to_hip":
                        units = " ratio"
                    
                    # Display the value with a green indicator
                    st.markdown(f"✅ **{display_name}:** {value}{units}")
            
            # Show missing fields
            missing_fields = [field for field in measurement_fields if field not in available_fields]
            if missing_fields:
                st.markdown("#### Missing Measurements")
                for field in missing_fields:
                    # Get display name from biomarkers definition
                    display_name = " ".join(word.capitalize() for word in field.split('_'))
                    for item in coach.biomarkers.get("categories", {}).get("measurements", {}).get("items", []):
                        if item["id"] == field:
                            display_name = item["name"]
                            break
                    
                    # Display as missing with a red indicator
                    st.markdown(f"❌ **{display_name}**")
            
            if not coach.user_data["measurements"] and not missing_fields:
                st.caption("No measurement data available")
        
        # Other data tab (lab results, capabilities)
        with tabs[4]:
            st.subheader("Other Data")
            
            # Lab Results
            lab_fields = expected_fields.get("lab_results", [])
            available_lab_fields = set(coach.user_data["lab_results"].keys())
            
            # Capabilities
            capability_fields = expected_fields.get("capabilities", [])
            available_capability_fields = set(coach.user_data["capabilities"].keys())
            
            # Combined completeness
            all_fields = lab_fields + capability_fields
            all_available = available_lab_fields.union(available_capability_fields)
            if all_fields:
                completeness = int(len(all_available.intersection(all_fields)) / len(all_fields) * 100)
                st.caption(f"Completeness: {completeness}%")
            
            # Lab Results
            if coach.user_data["lab_results"]:
                st.markdown("#### Available Lab Results")
                for key, value in coach.user_data["lab_results"].items():
                    display_name = " ".join(word.capitalize() for word in key.split('_'))
                    
                    # Add units where appropriate
                    units = ""
                    if key == "vitamin_d":
                        units = " ng/mL"
                    
                    st.markdown(f"✅ **{display_name}:** {value}{units}")
            
            # Show missing lab fields
            missing_lab_fields = [field for field in lab_fields if field not in available_lab_fields]
            if missing_lab_fields:
                st.markdown("#### Missing Lab Results")
                for field in missing_lab_fields:
                    # Get display name
                    display_name = " ".join(word.capitalize() for word in field.split('_'))
                    for item in coach.biomarkers.get("categories", {}).get("lab_results", {}).get("items", []):
                        if item["id"] == field:
                            display_name = item["name"]
                            break
                    
                    st.markdown(f"❌ **{display_name}**")
            
            # Capabilities
            if coach.user_data["capabilities"]:
                st.markdown("#### Available Capabilities")
                for key, value in coach.user_data["capabilities"].items():
                    display_name = " ".join(word.capitalize() for word in key.split('_'))
                    
                    # Add units where appropriate
                    units = ""
                    if key == "plank":
                        units = " sec"
                    elif key == "sit_and_reach":
                        units = " cm"
                    
                    st.markdown(f"✅ **{display_name}:** {value}{units}")
            
            # Show missing capability fields
            missing_capability_fields = [field for field in capability_fields if field not in available_capability_fields]
            if missing_capability_fields:
                st.markdown("#### Missing Capabilities")
                for field in missing_capability_fields:
                    # Get display name
                    display_name = " ".join(word.capitalize() for word in field.split('_'))
                    for item in coach.biomarkers.get("categories", {}).get("capabilities", {}).get("items", []):
                        if item["id"] == field:
                            display_name = item["name"]
                            break
                    
                    st.markdown(f"❌ **{display_name}**")
            
            if not coach.user_data["lab_results"] and not coach.user_data["capabilities"] and not missing_lab_fields and not missing_capability_fields:
                st.caption("No additional data available")

def show_completeness_indicators():
    """Show completeness indicators for all data categories."""
    st.header("Health Profile Completeness")
    
    # Get completeness data
    completeness_data = {}
    overall = 0
    
    for category in st.session_state.coach.biomarkers.get("categories", {}):
        display_name = st.session_state.coach.biomarkers["categories"][category]["display_name"]
        completeness = st.session_state.coach.calculate_category_completeness(category)
        completeness_data[display_name] = completeness
        
        # Show progress bar for each category
        percentage = int(completeness * 100)
        st.write(f"{display_name}: {percentage}%")
        st.progress(completeness)
    
    # Calculate and show overall completeness
    overall = st.session_state.coach.calculate_overall_completeness()
    overall_percentage = int(overall * 100)
    
    st.write("---")
    st.write(f"**Overall Completeness: {overall_percentage}%**")
    st.progress(overall)
    
    # Show radar chart if we have data in at least one category
    if overall > 0:
        st.write("---")
        radar_chart = draw_completeness_chart(completeness_data)
        st.pyplot(radar_chart)
    
    # Suggest next measurements
    if overall < 0.8:  # Only show suggestions if profile is less than 80% complete
        st.write("---")
        st.subheader("Suggested Next Measurements")
        
        # Use the formatted suggestions from coach
        suggestions_text = st.session_state.coach.format_missing_data_suggestions(limit=3)
        st.markdown(suggestions_text)

def show_daily_health_dashboard(user_id):
    """Show a dashboard of the user's daily health metrics if available."""
    if not st.session_state.db_initialized:
        return
    
    # Get daily health summary
    summary = get_daily_health_summary(user_id)
    
    if not summary:
        return
    
    st.header(f"Daily Health Metrics (Last {summary['days']} days)")
    
    # Create 4 columns for the metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Avg. Active Calories", f"{summary['avg_calories']}")
    
    with col2:
        st.metric("Avg. Steps", f"{int(summary['avg_steps']):,}")
    
    with col3:
        st.metric("Avg. Sleep (hrs)", f"{summary['avg_sleep']}")
    
    with col4:
        st.metric("Avg. Health Score", f"{summary['avg_score']}/100")
    
    # Get the data for plotting
    try:
        daily_data = st.session_state.db.get_daily_health_data(user_id, limit=14)
        
        if daily_data:
            # Reverse to get chronological order
            daily_data.reverse()
            
            # Extract data for plotting
            dates = [d['date'] for d in daily_data]
            scores = [d['daily_score'] for d in daily_data]
            
            # Create a simple line chart
            fig, ax = plt.subplots(figsize=(10, 3))
            ax.plot(dates, scores, marker='o', linestyle='-', color='#1f77b4')
            ax.set_title('Daily Health Scores')
            ax.set_ylabel('Score (0-100)')
            ax.set_ylim(0, 100)
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Rotate date labels for better readability
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            st.pyplot(fig)
    except Exception as e:
        st.error(f"Error plotting daily health data: {e}")

def main():
    """Main function to run the Bio Age Coach."""
    # Set page configuration
    st.set_page_config(page_title="Bio Age Coach", page_icon="🧬", layout="wide")
    
    # Initialize all session state variables at the start
    if "coach" not in st.session_state:
        st.session_state.coach = BioAgeCoach()
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "current_category" not in st.session_state:
        st.session_state.current_category = "biomarkers"
    
    if "selected_user_id" not in st.session_state:
        st.session_state.selected_user_id = None
    
    if "user_data_loaded" not in st.session_state:
        st.session_state.user_data_loaded = False
    
    if "category_options" not in st.session_state:
        st.session_state.category_options = {}
        for category_key, category_data in st.session_state.coach.biomarkers.get("categories", {}).items():
            st.session_state.category_options[category_key] = category_data.get("display_name", category_key)
    
    if "db_initialized" not in st.session_state:
        try:
            # Initialize database connector
            db_path = "data/test_database.db"
            if os.path.exists(db_path):
                st.session_state.db = DatabaseConnector(db_path)
                st.session_state.db_initialized = True
            else:
                st.session_state.db_initialized = False
        except Exception as e:
            st.session_state.db_initialized = False
            st.error(f"Failed to initialize database: {e}")
    
    # Main layout
    st.sidebar.title("🧬 Bio Age Coach")
    
    # User selection in sidebar if database is available
    if st.session_state.db_initialized:
        try:
            users = st.session_state.db.get_all_users()
            
            # User dropdown
            user_options = {user["id"]: f"{user['username']} ({user['email']})" for user in users}
            selected_user = st.sidebar.selectbox(
                "Select User",
                options=list(user_options.keys()),
                format_func=lambda x: user_options[x] if x in user_options else "Select a user",
                key="user_selector",
                index=0 if st.session_state.selected_user_id in user_options else None
            )
            
            # Handle user selection change
            if selected_user != st.session_state.selected_user_id:
                st.session_state.selected_user_id = selected_user
                if load_user_data(selected_user):
                    st.rerun()
            
            # Display the user's health data profile in the sidebar when a user is selected
            if st.session_state.selected_user_id:
                display_health_data_profile(st.session_state.coach)
                
        except Exception as e:
            st.sidebar.error(f"Error loading users: {e}")
            if st.sidebar.button("Retry Loading Users"):
                st.rerun()
    else:
        st.sidebar.warning("Database not initialized. Using manual data entry mode.")
        
        # Add a button to run the data generation script
        if st.sidebar.button("Generate Test Database"):
            try:
                import subprocess
                result = subprocess.run(["python", "scripts/generate_test_data.py"], capture_output=True, text=True)
                if result.returncode == 0:
                    st.sidebar.success("Test database generated successfully! Please restart the app.")
                else:
                    st.sidebar.error(f"Error generating test database: {result.stderr}")
            except Exception as e:
                st.sidebar.error(f"Error running script: {e}")
    
    # Main content area
    st.title("Bio Age Coach")
    
    # Show completeness indicators and daily health dashboard when a user is selected
    if st.session_state.db_initialized and st.session_state.selected_user_id:
        show_completeness_indicators()
        show_daily_health_dashboard(st.session_state.selected_user_id)
    
    # Only show the data entry form if:
    # 1. There's no database initialized, OR
    # 2. No user is selected
    if not st.session_state.db_initialized or not st.session_state.selected_user_id:
        # Category selector
        st.header("Enter Your Health Data")
        
        selected_category = st.selectbox(
            "Select data category",
            options=list(st.session_state.category_options.keys()),
            format_func=lambda x: st.session_state.category_options[x],
            key="category_selector",
            index=list(st.session_state.category_options.keys()).index(st.session_state.current_category)
        )
        
        # Update current category in session state
        if selected_category != st.session_state.current_category:
            st.session_state.current_category = selected_category
        
        # Create a form for the selected category
        with st.form(key=f"{selected_category}_form"):
            st.subheader(f"Enter {st.session_state.category_options[selected_category]} Values:")
            
            category_data = st.session_state.coach.biomarkers["categories"][selected_category]
            item_inputs = {}
            
            for item in category_data.get("items", []):
                # Check if there's already a value in user_data
                current_value = 0
                if item["id"] in st.session_state.coach.user_data[selected_category]:
                    current_value = st.session_state.coach.user_data[selected_category][item["id"]]
                
                item_inputs[item["id"]] = st.number_input(
                    f"{item['name']} ({item.get('unit', '')})",
                    min_value=0.0,
                    value=float(current_value) if current_value else 0.0,
                    help=item.get("description", ""),
                    key=f"input_{selected_category}_{item['id']}"
                )
            
            submit_button = st.form_submit_button(f"Add {st.session_state.category_options[selected_category]} to Chat")
            
            if submit_button:
                data_message = f"Here are my {st.session_state.category_options[selected_category].lower()} values:\n"
                values_added = False
                
                for item_id, value in item_inputs.items():
                    if value > 0:  # Only include items with values
                        for item in category_data.get("items", []):
                            if item["id"] == item_id:
                                data_message += f"- {item['name']}: {value} {item.get('unit', '')}\n"
                                # Update the coach's user_data
                                st.session_state.coach.user_data[selected_category][item_id] = value
                                values_added = True
                                break
                
                if values_added:
                    st.session_state.messages.append({"role": "user", "content": data_message})
                else:
                    st.warning(f"Please enter at least one {st.session_state.category_options[selected_category].lower()} value")
    
    # Chat interface
    st.header("Chat with Your Biological Age Coach")
    
    # Display messages
    for message in st.session_state.messages:
        if message["role"] != "system":  # Don't display system messages
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Get user input
    user_input = st.chat_input("Type your message here...")
    if user_input:
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Get response from coach
        with st.spinner("Thinking..."):
            response = st.session_state.coach.get_response(user_input)
        
        # Add assistant message to chat
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

if __name__ == "__main__":
    main() 