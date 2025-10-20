# Dockerfile multi-stage para PatCode
FROM python:3.11-slim as base

# Metadata
LABEL maintainer="PatCode Team"
LABEL version="0.5.0"
LABEL description="PatCode - AI-powered coding assistant"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN useradd -m -u 1000 patcode && \
    mkdir -p /app /app/logs /app/.patcode_cache && \
    chown -R patcode:patcode /app

WORKDIR /app

# Stage de dependencias
FROM base as dependencies

COPY requirements.txt requirements-dev.txt ./

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Stage de desarrollo
FROM dependencies as development

RUN pip install -r requirements-dev.txt

COPY --chown=patcode:patcode . .

USER patcode

CMD ["python", "main.py"]

# Stage de producción
FROM dependencies as production

COPY --chown=patcode:patcode . .

# Limpiar archivos innecesarios
RUN find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true && \
    find . -type f -name '*.pyc' -delete && \
    rm -rf tests/ docs/ .git/ .github/

USER patcode

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

CMD ["python", "main.py"]
