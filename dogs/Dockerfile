# ==========================================
# Stage 1: Builder — Install dependencies
# ==========================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies for lxml, newspaper3k
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2-dev \
    libxslt1-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


# ==========================================
# Stage 2: Runtime — Final image
# ==========================================
FROM python:3.11-slim as runtime

WORKDIR /app

# Install runtime dependencies (lxml, ffmpeg for yt-dlp)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 \
    libxslt1.1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Health check — bot should respond to /start
# AICODE-NOTE: Простая проверка процесса. Для продакшена можно добавить HTTP healthcheck endpoint.
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f "python main.py" || exit 1

# Default command
CMD ["python", "main.py"]

