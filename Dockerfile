FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    python-multipart \
    httpx \
    openai \
    pydantic \
    pydantic-settings \
    langgraph \
    langchain-core \
    chromadb \
    pymupdf \
    python-docx \
    jinja2 \
    pyyaml \
    loguru \
    rich \
    tiktoken \
    json-repair \
    chardet \
    markdown \
    aiofiles \
    static-files

COPY agent_core/ ./agent_core/
COPY fda_engine/ ./fda_engine/
COPY fda_cli.py .
COPY run.py .
COPY config.json .
COPY fda_frontend.html .

VOLUME ["/app/workspace", "/app/data"]

EXPOSE 8000

CMD ["python", "run.py"]
