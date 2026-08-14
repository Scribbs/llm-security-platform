"""
Job orchestrator – runs selected tools against the configured target
and stores results under /results/<job_id>/.
"""
import asyncio
import json
import logging
import os
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.services.runners import garak_runner, deepteam_runner, pyrit_runner, promptmap_runner

logger = logging.getLogger("lsap.orchestrator")

RUNNERS = {
    "garak": garak_runner.run,
    "deepteam": deepteam_runner.run,
    "pyrit": pyrit_runner.run,
    "promptmap": promptmap_runner.run,
    # Add more as they are implemented:
    # "llmfuzzer": llmfuzzer_runner.run,
    # "agentic-radar": ...,
}


async def _update_job(db: AsyncSession, job_id: str, **fields):
    sets = ", ".join(f"{k} = :{k}" for k in fields)
    fields["id"] = job_id
    fields["updated_at"] = datetime.now(timezone.utc)
    await db.execute(
        text(f"UPDATE lsap.jobs SET {sets}, updated_at = :updated_at WHERE id = :id"),
        fields,
    )
    await db.commit()


async def run_scan_job(job_id: str):
    """Background task entrypoint."""
    async with AsyncSessionLocal() as db:
        try:
            # Load job
            result = await db.execute(
                text("SELECT * FROM lsap.jobs WHERE id = :id"), {"id": job_id}
            )
            job = result.mappings().first()
            if not job:
                logger.error("Job %s not found", job_id)
                return

            await _update_job(
                db,
                job_id,
                status="running",
                started_at=datetime.now(timezone.utc),
                progress=json.dumps({"stage": "starting"}),
            )

            job_dir = Path(settings.RESULTS_DIR) / job_id
            job_dir.mkdir(parents=True, exist_ok=True)

            target_config = job["target_config"]
            if isinstance(target_config, str):
                target_config = json.loads(target_config)
            options = job["options"] or {}
            if isinstance(options, str):
                options = json.loads(options)

            tools: List[str] = job["tools_selected"] or []
            progress: Dict[str, Any] = {}
            overall_success = True

            for tool in tools:
                runner = RUNNERS.get(tool.lower())
                if not runner:
                    logger.warning("No runner for tool %s – skipping", tool)
                    progress[tool] = {"status": "skipped", "reason": "no runner implemented"}
                    continue

                progress[tool] = {"status": "running"}
                await _update_job(db, job_id, progress=json.dumps(progress))

                try:
                    tool_result = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: runner(
                            job_id=job_id,
                            job_dir=str(job_dir),
                            target_config=target_config,
                            options=options.get(tool, options.get(tool.lower(), {})),
                        ),
                    )
                    progress[tool] = {
                        "status": "completed" if tool_result.get("success") else "failed",
                        "summary": tool_result.get("summary", {}),
                    }

                    # Persist result row
                    await db.execute(
                        text("""
                            INSERT INTO lsap.results (job_id, tool_name, status, raw_path, summary)
                            VALUES (:job_id, :tool, :status, :raw_path, :summary::jsonb)
                        """),
                        {
                            "job_id": job_id,
                            "tool": tool,
                            "status": "completed" if tool_result.get("success") else "failed",
                            "raw_path": tool_result.get("raw_path"),
                            "summary": json.dumps(tool_result.get("summary", {})),
                        },
                    )
                    await db.commit()

                    if not tool_result.get("success"):
                        overall_success = False

                except Exception as e:
                    logger.exception("Tool %s failed for job %s", tool, job_id)
                    progress[tool] = {"status": "failed", "error": str(e)}
                    overall_success = False
                    await db.execute(
                        text("""
                            INSERT INTO lsap.results (job_id, tool_name, status, summary)
                            VALUES (:job_id, :tool, 'failed', :summary::jsonb)
                        """),
                        {
                            "job_id": job_id,
                            "tool": tool,
                            "summary": json.dumps({"error": str(e), "traceback": traceback.format_exc()}),
                        },
                    )
                    await db.commit()

                await _update_job(db, job_id, progress=json.dumps(progress))

            final_status = "completed" if overall_success else "failed"
            await _update_job(
                db,
                job_id,
                status=final_status,
                finished_at=datetime.now(timezone.utc),
                progress=json.dumps(progress),
            )
            logger.info("Job %s finished with status %s", job_id, final_status)

        except Exception as e:
            logger.exception("Orchestrator failed for job %s", job_id)
            try:
                await _update_job(
                    db,
                    job_id,
                    status="failed",
                    error_message=str(e),
                    finished_at=datetime.now(timezone.utc),
                )
            except Exception:
                pass
