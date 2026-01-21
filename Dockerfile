# Stage 1: Builder
FROM python:3.13-slim as builder

WORKDIR /app

# Installer dépendances système minimal pour construire les paquets Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements et installer dépendances Python dans un virtualenv
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime (final image - beaucoup plus léger)
FROM python:3.13-slim

WORKDIR /app

# Installer uniquement les dépendances runtime nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copier virtualenv du builder
COPY --from=builder /opt/venv /opt/venv

# Copier application
COPY . .

# Définir variables d'environnement
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=skyconnect.settings

# Créer répertoires nécessaires
RUN mkdir -p /app/staticfiles /app/media /app/logs

# Exposer port
EXPOSE 8000

# Commande de démarrage
CMD ["gunicorn", "skyconnect.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
