# Architecture

## High-level flow

1. User authenticates via Keycloak (OIDC / PKCE).
2. Frontend obtains an access token and calls the FastAPI backend.
3. Backend creates a job record in Postgres and launches a background task.
4. The orchestrator iterates over the selected tools, calling the corresponding runner.
5. Each runner:
   - Translates the common `TargetConfig` into the tool’s expected format.
   - Executes the tool (CLI or Python API).
   - Writes artifacts under `/results/<job_id>/<tool>/`.
   - Returns a structured summary.
6. Results are persisted in the `lsap.results` table.
7. The consolidator aggregates summaries into a single risk-oriented report.

## Why runners live inside the backend container (for now)

Many of the tools are Python libraries with overlapping (and sometimes conflicting) dependency trees. Running them in-process or via `subprocess` inside a single well-provisioned backend image keeps the first version simple.  

Dedicated tool containers (`garak-runner`, `deepteam-runner`, …) are defined under the `tools` profile and can be used later for isolation / resource limits / GPU assignment.

## Extending to additional tools

See `ADDING_A_TOOL.md`.

## Security considerations

- Target API keys should be treated as secrets. The current scaffold accepts them in the request body; for production store them encrypted or inject via a secret manager and never log them.
- Keycloak realm is imported at startup; change default passwords immediately.
- The backend currently performs only lightweight JWT claim extraction. Replace with proper JWKS validation against Keycloak.
- Results volume contains potentially sensitive model outputs and attack prompts – protect accordingly.
