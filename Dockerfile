# Multi-stage Dockerfile for Sequencing Data Management System
FROM python:3.11-slim as python-base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV FLASK_CONFIG=docker

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app directory and user
RUN useradd -m -u 1000 appuser
WORKDIR /app

# Copy Python requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY code/ ./code/
COPY templates/ ./templates/
COPY static/ ./static/

# Set the working directory to app root
WORKDIR /app

# Create directories for data processing
RUN mkdir -p /app/data /app/uploads /app/logs

# Set permissions
RUN chmod -R 755 /app

# Create volume mount point for user data
VOLUME ["/data"]

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/summary || exit 1

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
echo "🧬 Starting Sequencing Data Management System..."\n\
echo "🌐 Web interface will be available at http://localhost:5000"\n\
echo "📁 Mount your data directory to /data in the container"\n\
echo "💡 Example: docker run -p 5000:5000 -v /path/to/your/data:/data seqmanager"\n\
echo "📂 Checking file structure..."\n\
\n\
# Check required files\n\
if [ ! -f "/app/code/app.py" ]; then\n\
    echo "❌ Error: app.py not found"\n\
    exit 1\n\
fi\n\
\n\
if [ ! -f "/app/templates/index.html" ]; then\n\
    echo "❌ Error: index.html template not found"\n\
    exit 1\n\
fi\n\
\n\
if [ ! -d "/app/static" ]; then\n\
    echo "❌ Error: static directory not found"\n\
    exit 1\n\
fi\n\
\n\
echo "✅ File structure verified"\n\
\n\
# Set environment\n\
export PYTHONPATH="/app/code:$PYTHONPATH"\n\
export FLASK_CONFIG=docker\n\
\n\
cd /app\n\
echo "🚀 Starting Flask application..."\n\
exec python code/app.py' > /app/start.sh

RUN chmod +x /app/start.sh

# Start the application
CMD ["/app/start.sh"]
