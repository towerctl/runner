FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir . "towerctl-core[redis] @ git+https://github.com/towerctl/core@main"
CMD ["python", "-m", "runner.worker"]
