FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for python-magic and file conversion
RUN apt-get update && \
    apt-get install -y --no-install-recommends libmagic1 curl libreoffice-writer-nogui && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download and cache HF Model Weights first (so code changes don't bust the 1.6GB cache)
COPY download_models.py .
RUN python download_models.py

# Copy application code
COPY . .

# Make entrypoint executable (strip Windows line-endings if present)
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh

# Create storage directory
RUN mkdir -p /storage/reports

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
