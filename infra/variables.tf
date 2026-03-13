variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-1"
}

variable "s3_bucket_name" {
  description = "Nom du bucket S3 pour le datalake Iceberg (doit être globalement unique)"
  type        = string
  default     = "cfm-datalake-iceberg"
}

variable "glue_database" {
  description = "Nom de la database Glue (namespace Iceberg)"
  type        = string
  default     = "flights_db"
}
