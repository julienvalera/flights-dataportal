terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ---------------------------------------------------------------------------
# S3 bucket – stockage des données Iceberg
# ---------------------------------------------------------------------------

resource "aws_s3_bucket" "datalake" {
  bucket = var.s3_bucket_name

  tags = {
    Project     = "dataloader-v2"
    ManagedBy   = "terraform"
    Description = "Iceberg datalake bucket"
  }
}

resource "aws_s3_bucket_versioning" "datalake" {
  bucket = aws_s3_bucket.datalake.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "datalake" {
  bucket = aws_s3_bucket.datalake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "datalake" {
  bucket = aws_s3_bucket.datalake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle : expire les anciens snapshots Iceberg après 30 jours
resource "aws_s3_bucket_lifecycle_configuration" "datalake" {
  bucket = aws_s3_bucket.datalake.id

  rule {
    id     = "iceberg-metadata-cleanup"
    status = "Enabled"

    filter {
      prefix = "iceberg/"
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# ---------------------------------------------------------------------------
# Glue Database
# ---------------------------------------------------------------------------

resource "aws_glue_catalog_database" "flights_db" {
  name        = var.glue_database
  description = "Iceberg flights database"
}
