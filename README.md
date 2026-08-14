# LLM Security Assessment Platform (LSAP)

**Consolidated multi-tool LLM red-teaming & vulnerability assessment platform**

Protected by Keycloak SSO. Single interface to configure target models, select probes/tools, launch assessments, and view consolidated results from:

| Tool | Repo | Primary Focus |
|------|------|---------------|
| **Garak** | NVIDIA/garak | Broad LLM vulnerability scanning (jailbreaks, injection, leakage, toxicity, encoding, etc.) |
| **PyRIT** | microsoft/PyRIT | Multi-turn automated + human-led red teaming |
| **DeepTeam** | confident-ai/deepteam | OWASP LLM Top 10 aligned red teaming (120+ vulnerabilities) |
| **Promptmap** | utkusen/promptmap | Prompt injection & system prompt leakage |
| **LLMFuzzer** | mnns/LLMFuzzer | LLM API fuzzing (legacy but still useful) |
| **PurpleLlama** | meta-llama/PurpleLlama | Meta safety evaluations (Llama Guard, CyberSecEval components) |
| **Agentic Radar** | splx-ai/agentic-radar | Agentic / multi-agent system scanning |
| **Whistleblower** | Repello-AI/whistleblower | Reporting-oriented LLM security checks |
| **ART** | Trusted-AI/adversarial-robustness-toolbox | Adversarial robustness (broader ML) |
| **TextAttack** | QData/TextAttack | Text adversarial attacks |

> **Audience**: Security teams, red teamers, and AI engineers (especially those working in regulated / DoD / IC environments) who need a unified, self-hosted assessment capability rather than running ten separate CLIs.

---

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Browser / User │────▶│  Frontend (React)│────▶│  Keycloak (SSO)     │
└─────────────────┘     └────────┬─────────┘     └─────────────────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  Backend (FastAPI)│
                        │  - Auth middleware│
                        │  - Job orchestrator│
                        │  - Result consolidator│
                        └────────┬─────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
     ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
     │ Tool Runners   │ │ Shared Volume  │ │ Postgres/Redis │
     │ (garak, pyrit, │ │ /results       │ │ jobs + memory  │
     │  deepteam...)  │ │                │ │                │
     └────────────────┘ └────────────────┘ └────────────────┘
```

- **Keycloak** handles authentication & authorization (realm `lsap`).
- **Backend** accepts scan requests, enqueues jobs, executes tools (via subprocess or dedicated containers), stores raw + consolidated reports.
- **Frontend** provides a single pane of glass for model configuration, tool selection, progress, and results.
- All tools write artifacts under `/results/<job_id>/`.

---

## Quick Start

### Prerequisites
- Docker + Docker Compose v2
- At least 8–16 GB RAM recommended (some tools pull models / run LLM-as-judge)
- Optional: NVIDIA GPU if you want local model inference inside tools

### 1. Clone / Extract & Configure

```bash
cd llm-security-platform
cp .env.example .env
# Edit .env – set KEYCLOAK admin password, any default API keys you want pre-loaded, etc.
```

### 2. Bootstrap

```bash
./scripts/bootstrap.sh
```

This builds images, starts the stack, imports the Keycloak realm, and creates a default `admin` / `analyst` user.

### 3. Access

- **Frontend**: http://localhost:3000
- **Keycloak Admin**: http://localhost:8080 (admin / the password you set)
- **Backend API docs**: http://localhost:8000/docs

Default users (after bootstrap):
- `admin` / `admin123` (realm admin)
- `analyst` / `analyst123` (can run scans)

---

## Using the Platform

1. Log in via Keycloak.
2. Go to **New Assessment**.
3. Provide:
   - Target name
   - Generator / endpoint type (OpenAI-compatible, Azure, HuggingFace, custom REST, Ollama, etc.)
   - API key / base URL / model name
   - Which tools to run + any tool-specific options (probes for Garak, vulnerability categories for DeepTeam, etc.)
4. Launch. Jobs appear in the dashboard with live status.
5. When complete, open the consolidated report (Markdown + JSON) or drill into individual tool outputs.

---

## Tool Runner Notes

| Tool | Status in this scaffold | Notes |
|------|-------------------------|-------|
| Garak | Fully wired | Runs `garak` CLI, captures JSONL + HTML report |
| PyRIT | Wired (basic) | Uses `pyrit` Python API for simple single-turn + Crescendo-style examples |
| DeepTeam | Fully wired | Python API, OWASP framework support |
| Promptmap | Wired | CLI wrapper |
| LLMFuzzer | Basic | Config-driven; project is unmaintained |
| Others | Scaffold + entrypoints | Dockerfiles and runner stubs provided; extend as needed |

Many tools expect an OpenAI-compatible endpoint or a Python callback. The backend normalizes the user-supplied target into the format each tool expects.

---

## Extending

See `docs/ADDING_A_TOOL.md` and `docs/ARCHITECTURE.md`.

Typical pattern:
1. Add a Dockerfile under `tools/<name>/`.
2. Implement a runner function in `backend/app/services/runners/`.
3. Register it in the orchestrator and the frontend tool list.

---

## Security & Operational Notes

- All traffic after Keycloak is internal to the Docker network.
- API keys for target models are stored encrypted at rest (or only in memory for the job lifetime – configure in `.env`).
- Results volume should be backed by persistent storage in production.
- For air-gapped / IL4+ environments, pre-build images and remove external pulls.
- This is an assessment / red-team platform – treat the output as sensitive.

---

## License & Attribution

This scaffold is provided as a starting point for internal use.  
Individual tools retain their original licenses (Apache 2.0, MIT, etc.).  
Please respect the upstream projects and cite them when publishing results.

---

**Built for practical multi-tool LLM security assessment.**  
Questions / improvements welcome via issues or internal channels.
