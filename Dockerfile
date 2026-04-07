FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for WeasyPrint PDF generation
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libffi8 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/instance

EXPOSE 4345

ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Health check - polls the /health endpoint every 30s
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:4345/health')" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:4345", "--workers", "2", "--threads", "2", "app:app"]
