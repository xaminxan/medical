FROM python:3.11-slim

WORKDIR /app

ENV HF_ENDPOINT=https://hf-mirror.com
ENV HF_HOME=/app/models

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    pydantic \
    httpx \
    sentence-transformers \
    transformers \
    torch

COPY ml_server.py .

VOLUME ["/app/models"]

EXPOSE 8000

CMD ["python", "ml_server.py"]
