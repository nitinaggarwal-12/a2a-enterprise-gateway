# Multi-stage container for a2a.v1 gRPC Server
FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --gid 1001 appuser

COPY --from=builder /root/.local /home/appuser/.local
COPY protos ./protos
COPY server ./server
COPY a2a ./a2a

ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    GRPC_PORT=50051

USER appuser

EXPOSE 50051

CMD ["python", "-m", "server.server"]
