import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schemas import ScanRequest, JobSummary, JobDetail, JobStatus
from app.routers.auth import get_current_user
from app.services.orchestrator import run_scan_job

router = APIRouter()


@router.post("", response_model=JobSummary, status_code=202)
async def create_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new multi-tool assessment job and enqueue it."""
    job_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    # Persist job
    await db.execute(
        text("""
            INSERT INTO lsap.jobs
                (id, created_at, updated_at, created_by, status, target_name, target_config, tools_selected, options)
            VALUES
                (:id, :created_at, :updated_at, :created_by, :status, :target_name, :target_config::jsonb, :tools, :options::jsonb)
        """),
        {
            "id": str(job_id),
            "created_at": now,
            "updated_at": now,
            "created_by": user["preferred_username"],
            "status": JobStatus.pending.value,
            "target_name": request.target_name,
            "target_config": request.target.model_dump_json(),
            "tools": request.tools,
            "options": __import__("json").dumps(request.options),
        },
    )
    await db.commit()

    # Fire and forget
    background_tasks.add_task(run_scan_job, str(job_id))

    return JobSummary(
        id=job_id,
        created_at=now,
        updated_at=now,
        created_by=user["preferred_username"],
        status=JobStatus.pending,
        target_name=request.target_name,
        tools_selected=request.tools,
        progress={},
    )


@router.get("", response_model=List[JobSummary])
async def list_scans(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    result = await db.execute(
        text("""
            SELECT id, created_at, updated_at, created_by, status, target_name,
                   tools_selected, progress, error_message, started_at, finished_at
            FROM lsap.jobs
            ORDER BY created_at DESC
            LIMIT :limit
        """),
        {"limit": limit},
    )
    rows = result.mappings().all()
    return [
        JobSummary(
            id=r["id"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
            created_by=r["created_by"],
            status=JobStatus(r["status"]),
            target_name=r["target_name"],
            tools_selected=r["tools_selected"] or [],
            progress=r["progress"] or {},
            error_message=r["error_message"],
            started_at=r["started_at"],
            finished_at=r["finished_at"],
        )
        for r in rows
    ]


@router.get("/{job_id}", response_model=JobDetail)
async def get_scan(
    job_id: uuid.UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("SELECT * FROM lsap.jobs WHERE id = :id"),
        {"id": str(job_id)},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")

    # Fetch associated results
    res = await db.execute(
        text("SELECT tool_name, status, raw_path, summary FROM lsap.results WHERE job_id = :id"),
        {"id": str(job_id)},
    )
    tool_results = [
        {"tool": r["tool_name"], "status": r["status"], "raw_path": r["raw_path"], "summary": r["summary"]}
        for r in res.mappings().all()
    ]

    return JobDetail(
        id=row["id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        created_by=row["created_by"],
        status=JobStatus(row["status"]),
        target_name=row["target_name"],
        tools_selected=row["tools_selected"] or [],
        progress=row["progress"] or {},
        error_message=row["error_message"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        target_config=row["target_config"] if isinstance(row["target_config"], dict) else {},
        options=row["options"] if isinstance(row["options"], dict) else {},
        results=tool_results,
    )
