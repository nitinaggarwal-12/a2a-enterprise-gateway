FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY portal/ ./portal/
COPY option1_cloud_run_gateway/ ./option1_cloud_run_gateway/
COPY option2_grpc_service/ ./option2_grpc_service/
COPY option3_dual_plane/ ./option3_dual_plane/
COPY benchmarks/ ./benchmarks/
COPY docs/ ./docs/

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["sh", "-c", "uvicorn portal.app:app --host 0.0.0.0 --port ${PORT:-8080}"]
