FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends git curl && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/garak
RUN pip install --no-cache-dir "garak>=0.10.0"

ENV RESULTS_DIR=/results
VOLUME ["/results"]

# Default entrypoint – override with specific command at runtime
ENTRYPOINT ["python", "-m", "garak"]
CMD ["--help"]
