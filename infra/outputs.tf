output "s3_bucket_name" {
  description = "Nom du bucket S3 créé"
  value       = aws_s3_bucket.datalake.bucket
}

output "s3_bucket_arn" {
  description = "ARN du bucket S3"
  value       = aws_s3_bucket.datalake.arn
}

output "iceberg_location" {
  description = "Valeur à passer en S3_BUCKET pour le loader"
  value       = aws_s3_bucket.datalake.bucket
}

output "glue_database_name" {
  description = "Nom de la database Glue"
  value       = aws_glue_catalog_database.flights_db.name
}
