FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install torch from PyTorch's CPU index BEFORE the rest. sentence-transformers
# depends on torch, and the default PyPI wheel bundles the full CUDA runtime
# (cuda-toolkit, cublas, cudnn, nccl, triton) on both x86 and aarch64 - several
# GB of GPU libraries on a machine with no GPU. Installing the CPU build first
# means the dependency is already satisfied when requirements.txt is resolved.
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch

RUN pip install --no-cache-dir -r requirements.txt

COPY ./backend /app/backend
COPY ./evals /app/evals
COPY ./scripts /app/scripts
COPY ./alembic.ini /app/alembic.ini

ENV PYTHONPATH=/app/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
