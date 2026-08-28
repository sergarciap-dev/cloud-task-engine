from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import uuid
from datetime import datetime
from src.services.aws_service import aws_service

app = FastAPI(
    title="Cloud Task & Report Engine",
    description="API para procesamiento asíncrono de tareas y reportes en AWS",
    version="0.1.0"
)

class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    file_type: str = Field(..., pattern="^(csv|json)$")

class TaskResponse(BaseModel):
    task_id: str
    title: str
    status: str
    created_at: str
    upload_url: Optional[str] = None

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.post("/tasks", response_model=TaskResponse, status_code=201, tags=["Tasks"])
def create_task(payload: TaskCreateRequest):
    task_id = str(uuid.uuid4())
    file_key = f"uploads/{task_id}.{payload.file_type}"
    created_at = datetime.utcnow().isoformat()

    # Generar URL de carga directa a S3
    try:
        upload_url = aws_service.generate_presigned_upload_url(file_key=file_key)
    except Exception:
        upload_url = None

    task_item = {
        "taskId": task_id,
        "title": payload.title,
        "description": payload.description or "",
        "file_type": payload.file_type,
        "file_key": file_key,
        "status": "PENDING_UPLOAD",
        "created_at": created_at
    }

    # Persistir en DynamoDB
    try:
        aws_service.save_task(task_item)
    except Exception as e:
        # Si DynamoDB local no está inicializado, permitimos continuar informando el estado
        pass

    return {
        "task_id": task_id,
        "title": payload.title,
        "status": task_item["status"],
        "created_at": created_at,
        "upload_url": upload_url
    }