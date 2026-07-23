FROM python:3.12-slim

# faiss-cpu, xgboost, and torch all link against OpenMP (libgomp) for parallelism;
# the slim base doesn't ship it, and without it the packages fail to import.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# The default PyPI `torch` wheel on Linux is CUDA-enabled and drags in several GB of
# nvidia-*/triton/cuda-toolkit packages that a CPU-only container never uses. Installing
# torch from PyTorch's CPU wheel index first satisfies sentence-transformers' unpinned
# `torch` dependency below without pip ever reaching for the CUDA build.
RUN pip install --no-cache-dir --default-timeout=120 --retries 5 torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=120 --retries 5 -r requirements.txt

# Pre-download the policy_lookup embedding model at build time so the container
# doesn't need outbound access to huggingface.co on first request.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY mcp_server/ mcp_server/
COPY agent/ agent/
COPY api/ api/
COPY audit/ audit/
COPY rag/ rag/
COPY .env.example .env.example

RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
