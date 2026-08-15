from fastapi import APIRouter, HTTPException, Request

from app.scheduler import run_nightly_scheduler
from app.tasks import celery_app

router = APIRouter()


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    result = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": result.state,
        "result": result.result if result.successful() else None,
        "error": str(result.result) if result.failed() else None,
    }


@router.delete("/tasks/{task_id}")
async def revoke_task(task_id: str):
    celery_app.control.revoke(task_id, terminate=True)
    return {"task_id": task_id, "status": "REVOKED"}


@router.post("/scheduler/run")
async def trigger_scheduler(request: Request):
    if request.state.user.get("role") != "admin":
        raise HTTPException(403, "Admin only")
    await run_nightly_scheduler()
    return {"status": "scheduler ran"}
