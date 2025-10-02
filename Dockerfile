# Multi-stage build for production with distroless base
# Stage 1: Builder
FROM python:3.13-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster package management
RUN pip install --no-cache-dir uv

# Copy requirements and install dependencies
COPY requirements.txt .
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Stage 2: Base production image with distroless
FROM gcr.io/distroless/python3-debian12 as base

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set Python path
ENV PYTHONPATH=/usr/local/lib/python3.13/site-packages
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy application
WORKDIR /app
COPY --from=builder /app /app

# Run as non-root user (distroless default is nonroot uid 65532)
USER nonroot:nonroot

# Stage 3: Main Application
FROM base as app

# Expose port for main app
EXPOSE 8000

# Start the main application
CMD ["/usr/local/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Stage 4: MCP Server
FROM base as mcp-server

# Expose port for MCP server
EXPOSE 8002

# Start the MCP server
CMD ["/usr/local/bin/uvicorn", "tools.server:app", "--host", "0.0.0.0", "--port", "8002"]
