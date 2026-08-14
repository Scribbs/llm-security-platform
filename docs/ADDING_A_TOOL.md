# Adding a New Tool

1. **Create a runner** under `backend/app/services/runners/<tool>_runner.py` that implements:

   ```python
   def run(job_id: str, job_dir: str, target_config: dict, options: dict) -> dict:
       # returns {"success": bool, "raw_path": str|None, "summary": dict}
   ```

2. **Register** it in `backend/app/services/orchestrator.py`:

   ```python
   from app.services.runners import mytool_runner
   RUNNERS["mytool"] = mytool_runner.run
   ```

3. **(Optional)** Add a dedicated Dockerfile under `tools/mytool/` and a service in `docker-compose.yml` under the `tools` profile.

4. **Expose it in the UI** by adding an entry to `AVAILABLE_TOOLS` in `frontend/src/App.jsx`.

5. **Document** any required environment variables or special configuration in the main README.
