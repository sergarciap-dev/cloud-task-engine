import json
import boto3
from botocore.exceptions import ClientError
from src.core.config import settings

class AWSService:
    def __init__(self):
        client_kwargs = {
            "region_name": settings.AWS_REGION,
            "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY
        }
        if settings.AWS_ENDPOINT_URL:
            client_kwargs["endpoint_url"] = settings.AWS_ENDPOINT_URL

        self.dynamodb = boto3.resource("dynamodb", **client_kwargs)
        self.s3_client = boto3.client("s3", **client_kwargs)
        self.sqs_client = boto3.client("sqs", **client_kwargs)
        self.table = self.dynamodb.Table(settings.DYNAMODB_TABLE_NAME)

    def save_task(self, task_data: dict) -> dict:
        try:
            self.table.put_item(Item=task_data)
            return task_data
        except ClientError as e:
            raise RuntimeError(f"Error al guardar en DynamoDB: {e.response['Error']['Message']}")

    def update_task_status(self, task_id: str, status: str, result_summary: dict = None):
        """Actualiza el estado de la tarea una vez procesada."""
        update_expr = "SET #st = :status"
        expr_attr_names = {"#st": "status"}
        expr_attr_values = {":status": status}

        if result_summary:
            update_expr += ", #res = :result"
            expr_attr_names["#res"] = "result_summary"
            expr_attr_values[":result"] = json.dumps(result_summary)

        try:
            self.table.update_item(
                Key={"taskId": task_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=expr_attr_values
            )
        except ClientError as e:
            raise RuntimeError(f"Error al actualizar DynamoDB: {e.response['Error']['Message']}")

    def generate_presigned_upload_url(self, file_key: str, expiration: int = 3600) -> str:
        try:
            return self.s3_client.generate_presigned_url(
                ClientMethod="put_object",
                Params={"Bucket": settings.S3_BUCKET_NAME, "Key": file_key},
                ExpiresIn=expiration
            )
        except ClientError as e:
            raise RuntimeError(f"Error al generar presigned URL: {e.response['Error']['Message']}")

    def send_task_to_queue(self, message_body: dict):
        """Envía el evento de procesamiento a la cola Amazon SQS."""
        try:
            queue_url = self.sqs_client.get_queue_url(QueueName=settings.SQS_QUEUE_NAME)["QueueUrl"]
            self.sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(message_body)
            )
        except ClientError as e:
            raise RuntimeError(f"Error al enviar mensaje a SQS: {e.response['Error']['Message']}")

    def get_task(self, task_id: str) -> dict:
        """Obtiene el registro de una tarea desde DynamoDB."""
        try:
            response = self.table.get_item(Key={"taskId": task_id})
            return response.get("Item")
        except ClientError as e:
            raise RuntimeError(f"Error al consultar DynamoDB: {e.response['Error']['Message']}")    

aws_service = AWSService()