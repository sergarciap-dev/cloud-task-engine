import os
from pydantic import BaseModel

class Settings(BaseModel):
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_ENDPOINT_URL: str = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
    DYNAMODB_TABLE_NAME: str = os.getenv("DYNAMODB_TABLE_NAME", "TasksTable")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "reportes-bucket")
    
    # Credenciales ficticias para entorno local
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "test")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "test")

settings = Settings()