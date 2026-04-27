import os
import sys

# Add project root to sys.path so backend imports work
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.database import engine, Base
from backend.services.firestore_service import _get_firestore_client
from dotenv import load_dotenv

# Load env variables if they exist
load_dotenv(os.path.join("frontend", ".env.local"))

def clean_sqlite():
    db_path = "pqc_messenger.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print("Deleted local SQLite database.")
        except Exception as e:
            print(f"Could not delete SQLite database: {e}")
    else:
        print("Local SQLite database not found.")

def clean_firestore():
    try:
        # Force project ID
        if not os.environ.get("GCP_PROJECT_ID"):
            os.environ["GCP_PROJECT_ID"] = "pqsm-18197"
            
        # Use local service account credential if present
        sa_path = "backend/service-account.json"
        if os.path.exists(sa_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(sa_path)
            
        db = _get_firestore_client()
        
        # Delete all users
        users_ref = db.collection("users")
        docs = users_ref.stream()
        count = 0
        for doc in docs:
            doc.reference.delete()
            count += 1
        print(f"Deleted {count} users from Firestore.")
        
        # Also clean up old messages and media to fully reset the chat
        for coll in ["messages", "media"]:
            docs = db.collection(coll).stream()
            c = 0
            for doc in docs:
                doc.reference.delete()
                c += 1
            print(f"Deleted {c} items from '{coll}' collection in Firestore.")
            
    except Exception as e:
        print(f"Error connecting to Firestore: {e}")
        print("You may need to run this from Cloud Shell if local credentials are not set up.")

if __name__ == "__main__":
    clean_sqlite()
    clean_firestore()
