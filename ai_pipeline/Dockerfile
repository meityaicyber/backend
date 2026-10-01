FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY ai_pipeline/requirements.txt ./ai_reqs.txt
COPY standardTemp/requirements.txt ./std_reqs.txt
COPY standardTemp/requirements-models.txt ./model_reqs.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r ai_reqs.txt -r std_reqs.txt -r model_reqs.txt

COPY ai_pipeline /app
COPY standardTemp /app/standardTemp

ENV PYTHONPATH="/app/standardTemp:${PYTHONPATH}"
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
