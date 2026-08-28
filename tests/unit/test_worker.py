import pytest
from moto import mock_aws
import boto3
import os
from src.core.config import settings
from src.workers.processor import process_single_task

@pytest.fixture
def aws_credentials():
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

@pytest.fixture
def setup_dynamo_mock(aws_credentials):
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.create_table(
            TableName=settings.DYNAMODB_TABLE_NAME,
            KeySchema=[{"AttributeName": "taskId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "taskId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST"
        )
        table.put_item(Item={"taskId": "task-123", "status": "PENDING_UPLOAD"})
        yield table

def test_process_single_task_success(setup_dynamo_mock):
    message = {
        "taskId": "task-123",
        "file_key": "uploads/task-123.csv",
        "file_type": "csv"
    }
    result = process_single_task(message)
    assert result is True

    # Verificar que el registro en DynamoDB se actualizó a COMPLETED
    updated_item = setup_dynamo_mock.get_item(Key={"taskId": "task-123"}).get("Item")
    assert updated_item["status"] == "COMPLETED"
    assert "result_summary" in updated_item