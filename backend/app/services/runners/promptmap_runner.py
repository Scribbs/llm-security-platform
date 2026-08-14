"""
Promptmap runner – CLI wrapper for utkusen/promptmap.
"""
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger("lsap.runner.promptmap")


def run(job_id: str, job_dir: str, target_config: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
    out_dir = Path(job_dir) / "promptmap"
    out_dir.mkdir(parents=True, exist_ok=True)

    api_key = target_config.get("api_key") or os.getenv("OPENAI_API_KEY", "")
    model = target_config.get("model_name", "gpt-4o-mini")
    base_url = target_config.get("base_url")

    env = os.environ.copy()
    if api_key:
        env["OPENAI_API_KEY"] = api_key

    # promptmap typical usage is a CLI that takes a target description.
    # Exact flags depend on the version; this is a best-effort scaffold.
    cmd = [
        "promptmap",
        "--model", model,
        "--output", str(out_dir / "promptmap_results.json"),
    ]
    if base_url:
        cmd.extend(["--base-url", base_url])

    # If the binary is not on PATH, try python -m
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=options.get("timeout", 900),
            env=env,
        )
    except FileNotFoundError:
        cmd = ["python", "-m", "promptmap"] + cmd[1:]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=options.get("timeout", 900),
            env=env,
        )

    report_path = out_dir / "promptmap_results.json"
    if not report_path.exists():
        # Write whatever we captured
        with open(out_dir / "promptmap_stdout.txt", "w") as f:
            f.write(result.stdout or "")
            f.write("\n--- STDERR ---\n")
            f.write(result.stderr or "")
        report_path = out_dir / "promptmap_stdout.txt"

    summary = {
        "exit_code": result.returncode,
        "stdout_tail": (result.stdout or "")[-1500:],
        "stderr_tail": (result.stderr or "")[-1500:],
        "notes": "Promptmap run completed (or attempted). Review artifacts for injection findings.",
    }

    return {
        "success": result.returncode == 0,
        "raw_path": str(report_path),
        "summary": summary,
    }
