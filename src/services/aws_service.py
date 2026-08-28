import boto3
from botocore.exceptions import ClientError
from src.core.config import settings

class AWSService:
    def __init__(self):
        # Inicialización de clientes Boto3
        self.dynamodb = boto3.resource(
            "dynamodb",
            region_name=settings.AWS_REGION,
            endpoint_url=settings.AWS_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.s3_client = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            endpoint_url=settings.AWS_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.table = self.dynamodb.Table(settings.DYNAMODB_TABLE_NAME)

    def save_task(self, task_data: dict) -> dict:
        """Guarda el estado y metadatos de la tarea en DynamoDB."""
        try:
            self.table.put_item(Item=task_data)
            return task_data
        except ClientError as e:
            raise RuntimeError(f"Error al guardar en DynamoDB: {e.response['Error']['Message']}")

    def generate_presigned_upload_url(self, file_key: str, expiration: int = 3600) -> str:
        """Genera una URL prefirmada para que el cliente suba el archivo directamente a S3."""
        try:
            url = self.s3_client.generate_presigned_url(
                ClientMethod="put_object",
                Params={"Bucket": settings.S3_BUCKET_NAME, "Key": file_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            raise RuntimeError(f"Error al generar presigned URL en S3: {e.response['Error']['Message']}")

aws_service = AWSService()