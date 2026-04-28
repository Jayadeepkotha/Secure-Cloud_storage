import os
import shutil
import json
import boto3
from botocore.exceptions import ClientError

# Configuration - Matches your aws_client.py
BUCKET_NAME = "scs-encrypted-files-bucket"

def clean_local_folders():
    """Wipes artifacts, downloads, and logs."""
    folders = ['cloud_artifacts', 'downloads', 'logs']
    for folder in folders:
        if os.path.exists(folder):
            print(f"🧹 Clearing folder: {folder}...")
            # Deletes the folder and all its contents
            shutil.rmtree(folder)
            # Recreates an empty folder so the app doesn't crash next run
            os.makedirs(folder)
    print("✅ Local folders cleared.")

def clean_json_states():
    """Deletes the persistent local indices and state files."""
    state_files = ['local_df.json', 'local_di.json', 'local_di_state.json']
    for file in state_files:
        if os.path.exists(file):
            print(f"🗑️ Deleting state file: {file}...")
            os.remove(file)
    print("✅ Local JSON states deleted.")

def clean_s3_bucket():
    """Removes all objects from the S3 bucket."""
    print(f"☁️ Connecting to S3 to empty bucket: {BUCKET_NAME}...")
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(BUCKET_NAME)
    
    try:
        # Check if bucket exists before trying to delete
        bucket.objects.all().delete()
        print(f"✅ S3 Bucket '{BUCKET_NAME}' is now empty.")
    except ClientError as e:
        print(f"❌ AWS Error: {e}")
    except Exception as e:
        print(f"❌ Error accessing S3: {e}")

def run_total_wipe():
    print("!!! WARNING: THIS WILL PERMANENTLY DELETE ALL LOCAL AND CLOUD DATA !!!")
    confirm = input("Are you absolutely sure? (y/n): ")
    
    if confirm.lower() == 'y':
        clean_local_folders()
        clean_json_states()
        clean_s3_bucket()
        print("\n✨ Environment is now clean. Ready for a fresh Setup/Update.")
    else:
        print("❌ Cleanup aborted.")

if __name__ == "__main__":
    run_total_wipe()