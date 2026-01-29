from google.cloud import storage
import os
from dotenv import load_dotenv

load_dotenv()
bucket_name = os.getenv("GCS_BUCKET_NAME", "plosind-youtube-raw-data")
print(f"Checking bucket: {bucket_name}")

client = storage.Client()
bucket = client.bucket(bucket_name)

print("Listing first 5 blobs in the bucket:")
blobs = list(bucket.list_blobs(max_results=10))
for b in blobs:
    print(f"- {b.name}")
