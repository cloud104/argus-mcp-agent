# Multi-stage build for Main Application (production)
# Imagem otimizada contendo apenas código e dependências da aplicação principal

# Stage 1: Builder
FROM python:3.13-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster package management
RUN pip install --no-cache-dir uv

# Copy requirements and install dependencies (only what app needs)
COPY requirements.txt .
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Copy only what the app needs (exclude tools/)
COPY main.py .
COPY app/ ./app/
COPY prompts/ ./prompts/
COPY config/ ./config/

# Stage 2: Production image with Python slim (not distroless due to binary dependencies)
FROM python:3.13-slim

# Install runtime dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set Python path
ENV PYTHONPATH=/usr/local/lib/python3.13/site-packages
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy application code (only what's needed)
WORKDIR /app
COPY --from=builder /app/main.py ./main.py
COPY --from=builder /app/app ./app
COPY --from=builder /app/prompts ./prompts
COPY --from=builder /app/config ./config

# Create non-root user
RUN useradd -m -u 65532 -s /bin/bash nonroot && chown -R nonroot:nonroot /app
USER nonroot

# Expose port
EXPOSE 8000

# Start the main application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
