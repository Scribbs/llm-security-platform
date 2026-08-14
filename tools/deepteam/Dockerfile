FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends git curl && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/deepteam
RUN pip install --no-cache-dir deepteam openai

ENV RESULTS_DIR=/results
VOLUME ["/results"]

CMD ["python", "-c", "import deepteam; print('DeepTeam ready')"]
