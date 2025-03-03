import firebase_admin
from firebase_admin import credentials, db
import pandas as pd

# Initialize Firebase Admin SDK
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://forestvieworder-default-rtdb.firebaseio.com/'  # Replace with your database URL
})

# Fetch data from Firebase Realtime Database
def fetch_feedback():
    ref = db.reference('feedbacks')
    feedbacks = ref.get()

    if not feedbacks:
        print("No feedback found in the database.")
        return []

    # Format data into a list of dictionaries
    feedback_list = []
    for key, value in feedbacks.items():
        feedback_entry = {
            "Name": value.get("name", ""),
            "Email": value.get("email", ""),
            "Feedback": value.get("feedback", ""),
            "Timestamp": value.get("timestamp", "")
        }
        feedback_list.append(feedback_entry)

    return feedback_list

# Generate CSV report
def generate_csv_report(data, filename="feedback_report.csv"):
    if not data:
        print("No data to generate report.")
        return

    # Convert to pandas DataFrame
    df = pd.DataFrame(data)

    # Save to CSV
    df.to_csv(filename, index=False)
    print(f"Report generated successfully: {filename}")

if __name__ == "__main__":
    print("Fetching feedback from Firebase...")
    feedback_data = fetch_feedback()
    if feedback_data:
        print("Generating report...")
        generate_csv_report(feedback_data)
    else:
        print("No feedback data found. Exiting.")
