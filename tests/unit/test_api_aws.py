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
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

@pytest.fixture
def setup_aws_mock(aws_credentials):
    with mock_aws():
        # S3 Mock
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=settings.S3_BUCKET_NAME)

        # DynamoDB Mock
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        dynamodb.create_table(
            TableName=settings.DYNAMODB_TABLE_NAME,
            KeySchema=[{"AttributeName": "taskId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "taskId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST"
        )

        # SQS Mock
        sqs = boto3.client("sqs", region_name="us-east-1")
        sqs.create_queue(QueueName=settings.SQS_QUEUE_NAME)
        yield

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_create_task_success(setup_aws_mock):
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

def test_create_task_invalid_file_type():
    payload = {
        "title": "Archivo Malicioso",
        "file_type": "exe"
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 422

def test_get_task_success(setup_aws_mock):
    """Valida la consulta de una tarea existente."""
    # 1. Crear tarea previa
    payload = {"title": "Tarea de Consulta", "file_type": "json"}
    create_res = client.post("/tasks", json=payload)
    task_id = create_res.json()["task_id"]

    # 2. Consultar tarea
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert data["title"] == payload["title"]
    assert data["status"] == "PENDING_UPLOAD"

def test_get_task_not_found(setup_aws_mock):
    """Valida error 404 al consultar un ID inexistente."""
    response = client.get("/tasks/non-existent-id")
    assert response.status_code == 404
    assert response.json()["detail"] == "Tarea no encontrada"