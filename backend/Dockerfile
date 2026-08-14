FROM python:3.12-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-install the major tools so the backend can call them directly
RUN pip install --no-cache-dir \
    "garak>=0.10.0" \
    "deepteam" \
    "promptmap" || true

# PyRIT and others may need extra care; install best-effort
RUN pip install --no-cache-dir "pyrit" || echo "PyRIT install skipped / version conflict – runner will handle"

COPY app ./app
COPY runners ./runners

ENV PYTHONPATH=/app
ENV RESULTS_DIR=/results

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
