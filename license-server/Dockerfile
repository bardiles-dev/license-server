# ------------------------------
# Stage: builder (solo dependencias)
# ------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update -qq \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ------------------------------
# Stage: runtime (imagen final)
# ------------------------------
FROM python:3.12-slim AS runtime

# Usuario no privilegiado
ARG UID=1000
ARG GID=1000
RUN groupadd --gid ${GID} appgroup \
    && useradd --uid ${UID} --gid appgroup --shell /bin/sh --create-home appuser

WORKDIR /app

# Solo dependencias del builder (sin compiladores)
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Código de la aplicación
COPY app/ ./app/
COPY requirements.txt .

# public.pem: montar en runtime vía compose (volumen o bind) en /app/config/public.pem
RUN mkdir -p /app/data /app/config \
    && chown -R appuser:appgroup /app

USER appuser

EXPOSE 9000

# Producción: sin --reload
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000"]
