FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root system user for CIS container hardening
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -s /bin/bash -m appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY portal/ ./portal/
COPY option1_cloud_run_gateway/ ./option1_cloud_run_gateway/
COPY option2_grpc_service/ ./option2_grpc_service/
COPY option3_dual_plane/ ./option3_dual_plane/
COPY a2a_sdk/ ./a2a_sdk/
COPY benchmarks/ ./benchmarks/
COPY docs/ ./docs/

RUN chown -R appuser:appgroup /app

USER appuser

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["sh", "-c", "uvicorn portal.app:app --host 0.0.0.0 --port ${PORT:-8080}"]
