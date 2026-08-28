output "dynamodb_table_name" {
  description = "Nombre de la tabla DynamoDB"
  value       = aws_dynamodb_table.tasks_table.name
}

output "s3_bucket_name" {
  description = "Nombre del bucket S3 generado"
  value       = aws_s3_bucket.reports_bucket.bucket
}

output "sqs_queue_url" {
  description = "URL de la cola SQS"
  value       = aws_sqs_queue.tasks_queue.url
}