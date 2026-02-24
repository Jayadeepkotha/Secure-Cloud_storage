terraform {
  backend "s3" {
    bucket = "amzn-terraform-s3-bucket" # Put your exact S3 bucket name here
    key    = "state/terraform.tfstate"
    region = "us-east-1"
  }
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}


provider "aws" {
  region = "us-east-1"
}


# 1. Create the new Security Group
resource "aws_security_group" "web_sg" {
  name        = "web-server-sg"
  description = "Allow HTTP and SSH traffic"

  # Inbound rules (Who can connect TO your server)
  ingress {
    description = "Allow HTTP (Web Traffic)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # 0.0.0.0/0 means anyone on the internet can see the website
  }

  ingress {
    description = "Allow SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] 
  }

  # Outbound rules (What the server can connect out to)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1" # -1 means all protocols
    cidr_blocks = ["0.0.0.0/0"]
  }
}




resource "aws_instance" "my_servers" {
  count         = 1 # We are telling Terraform to build exactly 2 instances
  ami           = "ami-008622f29a0929d42" # Standard Ubuntu AMI
  instance_type = "t3.micro"

  # Attach the Security Group we just created above
  vpc_security_group_ids = [aws_security_group.web_sg.id]

  tags = {
    Name = "MyCustomWebUI"
  }
}


# 3. Print the Public IP so you can easily click it!
output "website_url" {
  description = "The public IP address of your Web UI"
  value       = "http://${aws_instance.my_web_server.public_ip}"
}


