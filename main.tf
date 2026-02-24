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

resource "aws_instance" "my_servers" {
  count         = 2 # We are telling Terraform to build exactly 2 instances
  ami           = "ami-0c7217cdde317cfec" # Standard Ubuntu AMI
  instance_type = "t2.micro"

  tags = {
    Name = "Server-${count.index + 1}"
  }
}