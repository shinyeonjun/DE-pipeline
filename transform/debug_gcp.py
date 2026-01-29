from google.cloud import storage
import google.auth
import os
from dotenv import load_dotenv

load_dotenv()

try:
    credentials, project_id = google.auth.default()
    print(f"Default Project ID: {project_id}")
    
    # User provided ID
    user_project_id = "deproject-482905"
    print(f"User provided Project ID: {user_project_id}")
    
    client = storage.Client(project=user_project_id)
    print("Listing buckets in this project...")
    buckets = list(client.list_buckets())
    if not buckets:
        print("No buckets found in this project.")
    else:
        for b in buckets:
            print(f"- {b.name}")
            
    # Check specific bucket
    bucket_name = os.getenv("GCS_BUCKET_NAME", "plosind-youtube-raw-data")
    print(f"Checking access to bucket: {bucket_name}")
    bucket = client.bucket(bucket_name)
    if bucket.exists():
        print(f"Bucket {bucket_name} exists and is accessible.")
    else:
        print(f"Bucket {bucket_name} NOT found in project {user_project_id}.")

except Exception as e:
    print(f"Error occurred: {e}")
