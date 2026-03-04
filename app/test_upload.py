import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# 🔥 CHANGE THIS TO YOUR TERRAFORM-CREATED BUCKET NAME
BUCKET_NAME = "scs-encrypted-files-bucket"

# Local file you want to upload
LOCAL_FILE = "requirements.txt"

# Name inside S3
S3_KEY = "requirements.txt"


def upload_file():
    s3 = boto3.client("s3", region_name="us-east-1")

    try:
        s3.upload_file(LOCAL_FILE, BUCKET_NAME, S3_KEY)
        print("✅ File uploaded successfully!")
    except FileNotFoundError:
        print("❌ Local file not found.")
    except NoCredentialsError:
        print("❌ AWS credentials not configured.")
    except ClientError as e:
        print(f"❌ AWS Error: {e}")


if __name__ == "__main__":
    upload_file()