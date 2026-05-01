terraform {
  backend "s3" {} 

  required_providers {
    aws   = { source = "hashicorp/aws", version = "~> 5.0" }
    local = { source = "hashicorp/local", version = "2.5.1" }
    tls   = { source = "hashicorp/tls", version = "4.0.5" }
  }
}

provider "aws" {
  region = var.aws_region
}

# --- 1. SSH KEY GENERATION ---
resource "tls_private_key" "main_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "generated_key" {
  key_name   = "access-key"
  public_key = tls_private_key.main_key.public_key_openssh
}

resource "local_file" "ssh_key" {
  content         = tls_private_key.main_key.private_key_pem
  filename        = "${path.module}/access.pem"
  file_permission = "0400"
}

# --- 2. S3 BUCKET FOR ENCRYPTED FILES ---
resource "aws_s3_bucket" "file_storage" {
  bucket        = var.file_storage_bucket_name
  force_destroy = true 

  tags = {
    Name = "EncryptedFileStorage"
  }
}

# --- 3. SECURITY GROUP (OPEN TO WORLD) ---
resource "aws_security_group" "web_sg" {
  name        = "project-sg-open"
  
  # Allow SSH from ANYWHERE
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] 
  }

  # Allow HTTP from ANYWHERE
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# --- 4. UBUNTU EC2 ---
resource "aws_instance" "ubuntu_server" {
  ami           = "ami-008622f29a0929d42" 
  instance_type = "t3.micro"
  key_name      = aws_key_pair.generated_key.key_name
  vpc_security_group_ids = [aws_security_group.web_sg.id]

  tags = {
    Name = "Ubuntu-EC2-Server"
  }
}

output "instance_ip" {
  value = aws_instance.ubuntu_server.public_ip
}

output "ssh_command" {
  value = "ssh -i access.pem ubuntu@${aws_instance.ubuntu_server.public_ip}"
}