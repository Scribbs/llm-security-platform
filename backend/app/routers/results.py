import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.routers.auth import get_current_user
from app.services.consolidator import build_consolidated_report

router = APIRouter()


@router.get("/{job_id}/consolidated")
async def get_consolidated(
    job_id: uuid.UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report = await build_consolidated_report(str(job_id), db)
    if report is None:
        raise HTTPException(status_code=404, detail="Job or results not found")
    return report


@router.get("/{job_id}/raw/{tool_name}")
async def get_raw_result(
    job_id: uuid.UUID,
    tool_name: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("SELECT raw_path FROM lsap.results WHERE job_id = :id AND tool_name = :tool"),
        {"id": str(job_id), "tool": tool_name},
    )
    row = result.mappings().first()
    if not row or not row["raw_path"]:
        raise HTTPException(status_code=404, detail="Raw result not found")

    path = Path(row["raw_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="File missing on disk")

    if path.suffix in {".json", ".jsonl", ".md", ".txt", ".html"}:
        return FileResponse(path, filename=path.name)
    return FileResponse(path)
