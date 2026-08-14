"""
DeepTeam runner – uses the deepteam Python API for red-teaming.
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger("lsap.runner.deepteam")


def run(job_id: str, job_dir: str, target_config: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
    out_dir = Path(job_dir) / "deepteam"
    out_dir.mkdir(parents=True, exist_ok=True)

    api_key = target_config.get("api_key") or os.getenv("OPENAI_API_KEY", "")
    model = target_config.get("model_name", "gpt-4o-mini")
    base_url = target_config.get("base_url")

    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    if base_url:
        os.environ["OPENAI_BASE_URL"] = base_url

    try:
        from deepteam import red_team
        from deepteam.frameworks import OWASPTop10
        # Optional specific vulnerabilities
        # from deepteam.vulnerabilities import Bias, Toxicity, ...
        # from deepteam.attacks.single_turn import PromptInjection

        # Build a simple model callback that talks to the target
        # For real OpenAI-compatible endpoints we can use litellm or openai client.
        import openai

        client = openai.OpenAI(
            api_key=api_key or "sk-placeholder",
            base_url=base_url or None,
        )

        def model_callback(input_text: str) -> str:
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": input_text}],
                    max_tokens=512,
                    temperature=0.0,
                )
                return resp.choices[0].message.content or ""
            except Exception as e:
                return f"[ERROR calling model: {e}]"

        framework = options.get("framework", "OWASPTop10")
        if framework == "OWASPTop10":
            risk_assessment = red_team(
                model_callback=model_callback,
                framework=OWASPTop10(),
            )
        else:
            # Fallback minimal run
            risk_assessment = red_team(
                model_callback=model_callback,
                framework=OWASPTop10(),
            )

        # Persist
        report_path = out_dir / "deepteam_report.json"
        # risk_assessment is typically a rich object; try to serialize what we can
        try:
            data = risk_assessment.to_dict() if hasattr(risk_assessment, "to_dict") else str(risk_assessment)
            if not isinstance(data, (dict, list)):
                data = {"raw": str(data)}
        except Exception:
            data = {"raw": str(risk_assessment)}

        with open(report_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        # Extract a simple risk level if present
        overall_risk = "unknown"
        if isinstance(data, dict):
            overall_risk = data.get("overall_risk") or data.get("risk_level") or data.get("score", "unknown")
            if isinstance(overall_risk, (int, float)):
                overall_risk = "high" if overall_risk > 0.7 else "medium" if overall_risk > 0.3 else "low"

        summary = {
            "framework": framework,
            "overall_risk": overall_risk,
            "report_path": str(report_path),
            "notes": "DeepTeam assessment completed. Inspect the JSON report for vulnerability breakdown.",
        }

        return {"success": True, "raw_path": str(report_path), "summary": summary}

    except ImportError as e:
        logger.error("deepteam not installed: %s", e)
        return {
            "success": False,
            "raw_path": None,
            "summary": {"error": f"deepteam package not available: {e}"},
        }
    except Exception as e:
        logger.exception("DeepTeam runner failed")
        return {"success": False, "raw_path": None, "summary": {"error": str(e)}}
