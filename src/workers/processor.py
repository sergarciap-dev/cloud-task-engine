import logging
from src.services.aws_service import aws_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TaskProcessor")


def process_single_task(message_body: dict):
    task_id = message_body.get("taskId")
    file_key = message_body.get("file_key")
    file_type = message_body.get("file_type")

    logger.info(f"Procesando tarea: {task_id} | Archivo: {file_key}")

    # Simulación de parsing y extracción de métricas
    simulated_summary = {
        "processed_rows": 1500,
        "format": file_type,
        "status": "VALIDATED",
    }

    # Actualizar estado final en DynamoDB
    aws_service.update_task_status(
        task_id=task_id, status="COMPLETED", result_summary=simulated_summary
    )
    logger.info(f"Tarea {task_id} finalizada exitosamente.")
    return True
