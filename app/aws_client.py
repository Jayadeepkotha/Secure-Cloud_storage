import boto3 
from botocore.exceptions import ClientError, NoCredentialsError
import os
from dotenv import load_dotenv

load_dotenv()

BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "fallback")
EC2_HOSTNAME = os.getenv("EC2_HOSTNAME", "127.0.0.1")

def get_s3_client():
    return boto3.client("s3", region_name="us-east-1") 

def upload_file(local_path, s3_key):
    s3 = get_s3_client()
    try:
        s3.upload_file(local_path, BUCKET_NAME, s3_key) 
        print(f"✅ {local_path} uploaded to S3 as {s3_key}")
        return True
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False

def download_file(s3_key, local_path):
    s3 = get_s3_client()
    try:
        s3.download_file(BUCKET_NAME, s3_key, local_path)
        print(f"✅ {s3_key} downloaded to {local_path}")
        return True
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False