FROM python:3.12-slim

WORKDIR /app

# System packages needed for pip builds + common native deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Rust/Cargo so packages that ship Rust extensions can compile
# when a prebuilt wheel is unavailable for this platform.
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable \
    && . "$HOME/.cargo/env" \
    && rustc --version && cargo --version
ENV PATH="/root/.cargo/bin:${PATH}"

# Upgrade packaging tools first
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Core backend dependencies (no optional LLM tools yet)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Tool SDKs – best-effort. Failures here must not break the image.
# Runners already handle ImportError / missing CLI gracefully.
RUN pip install --no-cache-dir "garak>=0.10.0" || echo "WARN: garak install failed – runner will report it"
RUN pip install --no-cache-dir "deepteam" || echo "WARN: deepteam install failed – runner will report it"
RUN pip install --no-cache-dir "promptmap" || echo "WARN: promptmap install failed – runner will report it"
RUN pip install --no-cache-dir "pyrit" || echo "WARN: pyrit install failed – runner will report it"

# Application code
COPY app ./app
# runners/ folder is optional in the scaffold; create empty dir if missing at build time
RUN mkdir -p /app/runners
COPY runners ./runners

ENV PYTHONPATH=/app
ENV RESULTS_DIR=/results

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
