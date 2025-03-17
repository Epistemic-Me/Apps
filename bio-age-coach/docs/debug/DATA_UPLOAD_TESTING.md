# Testing Data Upload Functionality

This document provides instructions on how to test the data upload functionality in the Bio Age Coach application.

## Sample Data Files

The following sample data files are provided for testing:

- `data/sample_sleep_data.csv`: Sample sleep data
- `data/sample_exercise_data.csv`: Sample exercise data
- `data/sample_nutrition_data.csv`: Sample nutrition data
- `data/sample_biometric_data.csv`: Sample biometric data

## Testing Steps

1. Start the Streamlit application:
   ```
   cd /path/to/bio-age-coach
   streamlit run app.py
   ```

2. In the chat interface, you'll see a file upload button directly integrated into the chat input area.

3. Click the file upload button and select one of the sample files from the `data` directory (e.g., `sample_sleep_data.csv`).

4. The application will automatically detect the type of data in the file based on its column names and process it accordingly. You don't need to manually specify the data type.

5. The application will create an observation context for the uploaded data and generate a response with insights.

6. You should see the active observation context in the sidebar, showing the relevancy score for the data type you uploaded.

7. Now you can ask questions related to the uploaded data, and the semantic router should route your queries to the appropriate agent based on the observation contexts.

## Data Type Detection

The application automatically detects the data type based on column names in the CSV file:

- **Sleep data**: Detected when columns contain terms like "sleep_hours", "deep_sleep", "rem_sleep", or "light_sleep"
- **Exercise data**: Detected when columns contain terms like "steps", "active_calories", or "exercise_minutes"
- **Nutrition data**: Detected when columns contain terms like "calories", "protein", "carbs", or "fats"
- **Biometric data**: Detected when columns contain terms like "weight", "systolic", "diastolic", or "body_fat_percentage"

## Example Queries

After uploading sleep data:
- "How is my sleep quality?"
- "Am I getting enough deep sleep?"

After uploading exercise data:
- "How active have I been?"
- "What's my average step count?"

After uploading nutrition data:
- "How is my protein intake?"
- "Am I eating too many carbs?"

After uploading biometric data:
- "How is my blood pressure?"
- "What's my resting heart rate?"

## Troubleshooting

If you encounter any issues:

1. Check the console output for error messages.
2. Verify that the data format in your CSV file matches the expected format.
3. Make sure the file contains the appropriate columns for automatic data type detection.
4. Restart the application if necessary. 