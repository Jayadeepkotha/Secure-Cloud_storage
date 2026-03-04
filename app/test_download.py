import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# 🔥 Replace with your bucket name
BUCKET_NAME = "scs-encrypted-files-bucket"

# Name of the file inside S3
S3_KEY = "requirements.txt"

# Name you want to save locally
LOCAL_FILE = "downloaded_requirements_from_s3.txt"


def download_file():
    s3 = boto3.client("s3", region_name="us-east-1")

    try:
        s3.download_file(BUCKET_NAME, S3_KEY, LOCAL_FILE)
        print("✅ File downloaded successfully!")
    except NoCredentialsError:
        print("❌ AWS credentials not configured.")
    except ClientError as e:
        print(f"❌ AWS Error: {e}")


if __name__ == "__main__":
    download_file()