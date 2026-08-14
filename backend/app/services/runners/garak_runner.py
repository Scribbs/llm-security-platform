"""
Garak runner – executes NVIDIA garak against the configured target.
"""
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger("lsap.runner.garak")


def run(job_id: str, job_dir: str, target_config: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns:
        {
            "success": bool,
            "raw_path": str | None,
            "summary": dict
        }
    """
    out_dir = Path(job_dir) / "garak"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Map target to garak generator
    ttype = target_config.get("type", "openai")
    model = target_config.get("model_name", "gpt-4o-mini")
    api_key = target_config.get("api_key") or os.getenv("OPENAI_API_KEY", "")
    base_url = target_config.get("base_url")

    # Environment for the subprocess
    env = os.environ.copy()
    if api_key:
        env["OPENAI_API_KEY"] = api_key
    if base_url:
        env["OPENAI_BASE_URL"] = base_url

    probes = options.get("probes", "encoding,promptinject,dan,lmrc")
    if isinstance(probes, list):
        probes = ",".join(probes)

    # Build command. Garak supports many generators; we start with openai / rest.
    cmd = [
        "python", "-m", "garak",
        "--target_type", "openai" if ttype in ("openai", "azure_openai", "ollama") else "rest",
        "--target_name", model,
        "--probes", probes,
        "--report_prefix", str(out_dir / "report"),
        "--generations", str(options.get("generations", 1)),
    ]

    # For Ollama or custom base_url we can pass generator options via config or env.
    # Simplified for scaffold – extend as needed.

    logger.info("Running garak for job %s: %s", job_id, " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=options.get("timeout", 1800),
            env=env,
            cwd=str(out_dir),
        )

        # Collect artifacts
        report_files = list(out_dir.glob("report*.jsonl")) + list(out_dir.glob("*.report.jsonl"))
        html_files = list(out_dir.glob("*.html"))
        raw_path = str(report_files[0]) if report_files else None

        # Simple summary extraction
        fail_count = 0
        total = 0
        if report_files:
            try:
                with open(report_files[0]) as f:
                    for line in f:
                        total += 1
                        entry = json.loads(line)
                        # Garak marks hits / fails in various ways depending on version
                        if entry.get("status") == 1 or entry.get("detector_result", {}).get("pass") is False:
                            fail_count += 1
            except Exception as e:
                logger.warning("Could not parse garak report: %s", e)

        summary = {
            "exit_code": result.returncode,
            "stdout_tail": result.stdout[-2000:] if result.stdout else "",
            "stderr_tail": result.stderr[-2000:] if result.stderr else "",
            "total_entries": total,
            "fail_count": fail_count,
            "failed_probes": fail_count,  # alias used by consolidator
            "probes_requested": probes,
            "artifacts": [str(p) for p in report_files + html_files],
        }

        success = result.returncode == 0 or total > 0  # garak may return non-zero on findings
        return {"success": success, "raw_path": raw_path, "summary": summary}

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "raw_path": None,
            "summary": {"error": "garak timed out", "timeout": options.get("timeout", 1800)},
        }
    except Exception as e:
        logger.exception("garak runner error")
        return {"success": False, "raw_path": None, "summary": {"error": str(e)}}
