# Secure Cloud Storage (SCS)

Secure Cloud Storage is a lightweight Flask-based prototype for storing files in Amazon S3 while keeping the file contents encrypted on the client side and searchable through a local keyword index.

The project is built to demonstrate a simple searchable-encryption style workflow:

- encrypt files before they leave the local machine
- upload only ciphertext to S3
- maintain local metadata for keyword search
- download and decrypt files only when the user selects a result

## Project Motive

Traditional cloud storage is convenient, but it usually assumes the storage provider can access file contents or metadata. This project explores a safer model where:

- the cloud stores encrypted file blobs only
- searchable metadata is maintained locally
- decryption happens only on the client side

In short, SCS is meant to be a practical learning project around secure cloud storage, searchable encryption ideas, and simple AWS-backed deployment.

## How It Works

1. A user uploads a file through the Flask web interface.
2. The client extracts useful keywords from the filename and, for PDFs, from file text.
3. The file is encrypted locally using AES-GCM.
4. The encrypted file is saved as a cloud artifact and uploaded to an S3 bucket.
5. Local JSON files track:
   - a forward index: file -> keywords
   - an inverted index: keyword -> encrypted cloud object
   - local keyword state used by the prototype search flow
6. During search, the app looks up the keyword in the local inverted index.
7. When a file is selected, the encrypted object is downloaded from S3 and decrypted locally before being returned to the browser.

## Architecture

The project has three main layers:

- `app/`: Flask app, encryption logic, indexing logic, S3 client helpers, UI templates, and local scripts
- `infrastructure/terraform/`: AWS infrastructure definition for the S3 bucket, EC2 instance, and security group
- `.github/workflows/`: GitHub Actions workflow for Terraform deployment

## Module Guide

### Application Core

| Module | Purpose |
| --- | --- |
| `app/app.py` | Main Flask application. Exposes routes for the home page, upload flow, search flow, and download/decrypt flow. |
| `app/scs_client.py` | Core upload pipeline. Extracts keywords, updates local indices, encrypts the file, creates a cloud object key, and uploads ciphertext to S3. |
| `app/scs_search.py` | Core retrieval pipeline. Searches the local inverted index, downloads ciphertext from S3, decrypts it locally, and restores the original file. |
| `app/encryption.py` | Cryptographic helper module. Derives keys from a master key and encrypts/decrypts file content with AES-GCM. |
| `app/aws_client.py` | Thin AWS wrapper for S3 upload and download operations. |
| `app/scs_cleanup.py` | Cleanup utility that clears local artifacts, local index/state files, and optionally empties the S3 bucket. |

### Search / State Helpers

| Module | Purpose |
| --- | --- |
| `app/hexie.py` | Local state helper for trapdoor-style lookup data. Loads keyword state and derives a keyword-specific search token. |
| `app/jianding.py` | Present but currently empty. Likely reserved for future verification or integrity-related logic. |

### UI

| File | Purpose |
| --- | --- |
| `app/templates/index.html` | Landing page for the web interface. |
| `app/templates/upload.html` | Upload screen with progress feedback for local encryption and S3 upload. |
| `app/templates/search.html` | Search screen for keyword lookup, result display, and file retrieval. |
| `app/static/style.css` | Shared styling for the Flask web interface. |

### Infrastructure and Automation

| File | Purpose |
| --- | --- |
| `infrastructure/terraform/main.tf` | Provisions the AWS provider, S3 bucket, EC2 instance, and security group. |
| `infrastructure/terraform/variables.tf` | Reserved for Terraform input variables. Currently empty. |
| `infrastructure/terraform/outputs.tf` | Reserved for Terraform outputs. Currently empty because the main Terraform file already contains the public URL output. |
| `.github/workflows/deploy.yml` | GitHub Actions workflow that runs `terraform init` and `terraform apply` on pushes to `main`. |

### Supporting Files

| File | Purpose |
| --- | --- |
| `app/requirements.txt` | Python dependencies for the Flask app. |
| `app/run_test.py` | Manual end-to-end test script intended for encryption/upload/download verification. |
| `comands.txt` | Short deployment notes for the Terraform workflow. |
| `LICENSE` | MIT license for the project. |

## Local Data Produced by the App

The app creates and updates a few local files and folders while running:

- `local_df.json`: forward index of files and extracted keywords
- `local_di.json`: inverted index used for search
- `local_di_state.json`: local keyword state for the prototype search flow
- `cloud_artifacts/`: encrypted files before or during upload
- `downloads/`: downloaded encrypted files and restored plaintext files
- `temp_uploads/`: temporary uploaded files received by Flask

These files are important because the searchable metadata lives locally, not in S3.

## Setup

### Requirements

- Python 3.10+
- AWS account and valid AWS credentials
- An S3 bucket named `scs-encrypted-files-bucket` or matching updates in the code

### Install

```bash
cd app
pip install -r requirements.txt
```

### Run the Flask App

```bash
cd app
python app.py
```

Open `http://127.0.0.1:5000` in the browser.

## Deployment

Infrastructure is managed with Terraform in `infrastructure/terraform/`.

The current Terraform setup provisions:

- an S3 bucket for encrypted files
- an EC2 instance for hosting
- a security group allowing HTTP, HTTPS, and restricted SSH access

GitHub Actions deployment is defined in `.github/workflows/deploy.yml` and runs automatically on pushes to `main`.

## Notes and Current Limitations

- Search is performed against the local inverted index, not directly against encrypted data in S3.
- The master key in `app/encryption.py` is hardcoded for prototype/testing use and should be replaced with proper secret management in any serious deployment.
- Some files, such as `app/jianding.py`, `variables.tf`, and `outputs.tf`, are placeholders or partially prepared for future expansion.
- The project demonstrates the workflow clearly, but it is still a prototype rather than a production-ready secure storage system.

## License

This project is licensed under the MIT License. See `LICENSE` for details.
