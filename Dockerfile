FROM python:3.11-slim

# Set working directory
WORKDIR /jobfind

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    FLASK_ENV=production

# Install system dependencies (minimal)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY app/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /jobfind

# Expose port
EXPOSE 5001

# Run with gunicorn (production)
CMD ["gunicorn", "-k", "eventlet", "-w", "1", "main:app", "--bind", "0.0.0.0:${PORT:-5001}", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]