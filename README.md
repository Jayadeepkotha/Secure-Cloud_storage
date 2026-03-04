# Secure Cloud Storage (SCS) Project

## Overview
The Secure Cloud Storage (SCS) project is designed to provide a secure and scalable cloud-based solution for file storage and web hosting. This repository contains the application code, infrastructure as code (IaC) using Terraform, and GitHub workflows for CI/CD.

---

## Repository Structure

### 1. **Application Code** (`app/`)
This folder contains the Python application code for the project. Key files include:

- **`app.py`**: The main entry point for the application. (Currently empty, awaiting implementation.)
- **`aws_client.py`**: Handles interactions with AWS services such as S3.
- **`encryption.py`**: Provides encryption utilities to ensure secure file storage.
- **`hexie.py`**: (Purpose not specified, likely a utility module.)
- **`jianding.py`**: (Purpose not specified, likely a utility module.)
- **`test_download.py`**: Contains test cases for the file download functionality.
- **`test_upload.py`**: Contains test cases for the file upload functionality.
- **`static/`**: Holds static assets like CSS, JavaScript, and images.
- **`templates/`**: Contains HTML templates for the web application.
  - `index.html`: The homepage.
  - `search.html`: The search page.
  - `upload.html`: The file upload page.

### 2. **Infrastructure Code** (`infrastructure/terraform/`)
This folder contains Terraform configuration files to define and manage the cloud infrastructure:

- **`main.tf`**: Defines the AWS resources:
  - **S3 Bucket**: `scs-encrypted-files-bucket` for secure file storage. 
    - **Important**: `force_destroy = true` is set, which allows the bucket to be deleted even if it contains objects. Use with caution in production.
  - **Security Group**: `web-server-sg` to allow HTTP, HTTPS, and SSH traffic.
    - HTTP and HTTPS are open to the world (`0.0.0.0/0`).
    - SSH is restricted to a specific IP address.
  - **EC2 Instance**: A web server running on a `t3.micro` instance with an Ubuntu AMI.
    - The public IP of the instance is output for easy access.
- **`outputs.tf`**: Specifies the outputs of the Terraform configuration (e.g., public IP).
- **`variables.tf`**: Defines input variables for the Terraform configuration.

### 3. **GitHub Workflows** (`.github/workflows/`)
Automated CI/CD workflows for managing the infrastructure:

- **`deploy.yml`**: Deploys the infrastructure automatically on a push to the `main` branch.
  - Steps:
    1. Check out the repository.
    2. Configure AWS credentials using GitHub secrets.
    3. Initialize and apply the Terraform configuration.
- **`destroy.yml`**: Provides a manual workflow to destroy the infrastructure.
  - Steps:
    1. Check out the repository.
    2. Configure AWS credentials using GitHub secrets.
    3. Initialize and destroy the Terraform configuration.

---

## Key Points
- **S3 Bucket**: The `force_destroy = true` setting allows deletion of the bucket even if it contains objects. This is useful for development but should be handled carefully in production.
- **Security Group**: HTTP and HTTPS traffic are open to the world, while SSH access is restricted to a specific IP.
- **GitHub Secrets**: AWS credentials are securely stored as GitHub secrets and used in workflows.
- **Terraform State**: The Terraform state is stored in an S3 bucket (`amzn-terraform-s3-bucket`) for remote state management.

---

## How to Use

### Prerequisites
- AWS account with appropriate permissions.
- Terraform installed locally.
- Python environment set up (e.g., using the `Myenv` virtual environment).

### Deployment
1. Push changes to the `main` branch to trigger the `deploy.yml` workflow.
2. Monitor the workflow in the GitHub Actions tab.
3. Access the web server using the public IP output by Terraform.

### Destruction
1. Trigger the `destroy.yml` workflow manually from the GitHub Actions tab.
2. Confirm the destruction of resources.

---

## Future Work
- Implement the application logic in `app.py`.
- Add more robust testing and monitoring.
- Secure the S3 bucket with encryption and access policies.
- Optimize the Terraform configuration for production use.

---

## License
This project is licensed under the terms of the [LICENSE](LICENSE) file.