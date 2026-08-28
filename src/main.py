from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Any
import uuid
from datetime import datetime, timezone
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

class TaskDetailResponse(BaseModel):
    task_id: str
    title: str
    description: Optional[str] = None
    file_type: str
    file_key: str
    status: str
    created_at: str
    result_summary: Optional[Any] = None

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.post("/tasks", response_model=TaskResponse, status_code=201, tags=["Tasks"])
def create_task(payload: TaskCreateRequest):
    task_id = str(uuid.uuid4())
    file_key = f"uploads/{task_id}.{payload.file_type}"
    created_at = datetime.now(timezone.utc).isoformat()

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

    try:
        aws_service.save_task(task_item)
        aws_service.send_task_to_queue(task_item)
    except Exception:
        pass

    return {
        "task_id": task_id,
        "title": payload.title,
        "status": task_item["status"],
        "created_at": created_at,
        "upload_url": upload_url
    }

@app.get("/tasks/{task_id}", response_model=TaskDetailResponse, tags=["Tasks"])
def get_task(task_id: str):
    """Obtiene el estado actual y resultado de una tarea."""
    item = aws_service.get_task(task_id)
    if not item:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    return {
        "task_id": item["taskId"],
        "title": item["title"],
        "description": item.get("description"),
        "file_type": item["file_type"],
        "file_key": item["file_key"],
        "status": item["status"],
        "created_at": item["created_at"],
        "result_summary": item.get("result_summary")
    }