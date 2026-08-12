FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir . "towerctl-core[redis] @ git+https://github.com/towerctl/core@v0.1.1"
CMD ["python", "-m", "runner.worker"]
