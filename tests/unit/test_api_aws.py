import pytest
from fastapi.testclient import TestClient
from moto import mock_aws
import boto3
import os

from src.main import app
from src.core.config import settings

client = TestClient(app)

@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

@pytest.fixture
def setup_aws_mock(aws_credentials):
    """Crea los recursos mockeados de S3 y DynamoDB en memoria."""
    with mock_aws():
        # Inicializar S3 mock
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=settings.S3_BUCKET_NAME)

        # Inicializar DynamoDB mock
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        dynamodb.create_table(
            TableName=settings.DYNAMODB_TABLE_NAME,
            KeySchema=[{"AttributeName": "taskId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "taskId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST"
        )
        yield

def test_health_check():
    """Valida que el endpoint de salud responda 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_create_task_success(setup_aws_mock):
    """Valida la creación exitosa de una tarea con URL de subida."""
    payload = {
        "title": "Procesamiento de Métricas",
        "description": "Reporte mensual de ventas",
        "file_type": "csv"
    }
    response = client.post("/tasks", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["status"] == "PENDING_UPLOAD"
    assert "task_id" in data
    assert "upload_url" in data
    assert "reportes-bucket" in data["upload_url"]

def test_create_task_invalid_file_type():
    """Valida que falle si se envía una extensión no permitida (caso de borde/negativo)."""
    payload = {
        "title": "Archivo Malicioso",
        "file_type": "exe"
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 422  # Error de validación Pydantic