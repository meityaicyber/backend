# Builder Stage
FROM python:3.11-slim as builder
WORKDIR /app

# We will create requirements.txt in Phase 4.
# For now, we touch it so the build doesn't fail.
RUN touch requirements.txt
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt || true

# Runtime Stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/* || true
COPY . .

# Run the Worker
CMD ["python", "main.py"]
