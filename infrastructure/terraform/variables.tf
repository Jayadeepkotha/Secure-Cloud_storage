variable "aws_region" {
  default = "us-east-1"
}

variable "file_storage_bucket_name" {
  type        = string
  description = "Unique name for the file storage S3 bucket"
}