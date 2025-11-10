FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Copy service account key if needed (optional, better to use Workload Identity)
# COPY keys/service-account.json /app/keys/

# Cloud Run sets PORT env var
ENV PORT=8080

# Run the FastAPI app with uvicorn
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 1