# 🐳 SKYCONNECT Docker Setup Guide

## Prérequis
- Docker Desktop installé ([https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop))
- 4GB RAM minimum alloué à Docker
- Clés Google OAuth (voir `.env.example`)

## Installation & Démarrage

### 1️⃣ Configuration initiale
```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer .env avec tes paramètres (surtout GOOGLE_OAUTH_CLIENT_ID et DB_PASSWORD)
nano .env
```

### 2️⃣ Construire et démarrer les conteneurs
```bash
# Build l'image Docker
docker-compose build

# Démarrer les services
docker-compose up -d
```

### 3️⃣ Initialiser la base de données
```bash
# Appliquer les migrations
docker-compose exec web python manage.py migrate

# Créer un superuser (optionnel)
docker-compose exec web python manage.py createsuperuser

# Charger les fixtures (si applicable)
docker-compose exec web python manage.py loaddata fixtures/*
```

### 4️⃣ Accéder à l'application
- **Frontend:** http://localhost:80
- **Admin Django:** http://localhost:80/admin/
- **API (si applicable):** http://localhost:80/api/

## Commandes utiles

### Démarrer/Arrêter
```bash
# Démarrer
docker-compose up -d

# Arrêter
docker-compose down

# Arrêter et supprimer les volumes (données)
docker-compose down -v
```

### Logs & Débogage
```bash
# Voir les logs (tous les services)
docker-compose logs -f

# Logs d'un service spécifique
docker-compose logs -f web
docker-compose logs -f db

# Accéder à la console Django
docker-compose exec web python manage.py shell
```

### Base de données
```bash
# Backup de la base PostgreSQL
docker-compose exec db pg_dump -U skyconnect skyconnect > backup.sql

# Restore
docker-compose exec -T db psql -U skyconnect skyconnect < backup.sql

# Accéder à psql directement
docker-compose exec db psql -U skyconnect skyconnect
```

### Gestion des fichiers
```bash
# Accéder aux fichiers media uploadés
docker-compose exec web ls -la media/

# Accéder aux fichiers static
docker-compose exec web ls -la staticfiles/
```

## Architecture

```
┌─────────────────────────────────────────┐
│         Nginx (Reverse Proxy)           │
│         Port: 80, 443                   │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼───────┐   ┌────────▼──────────┐
│  Django App   │   │  Static & Media   │
│  Gunicorn     │   │   (Cached)        │
│  Port: 8000   │   └───────────────────┘
└───────┬───────┘
        │
┌───────▼──────────────┐
│  PostgreSQL 16       │
│  Port: 5432          │
│  Volumes: persisted  │
└──────────────────────┘
```

## Variables d'environnement importantes

| Variable | Description | Exemple |
|----------|-------------|---------|
| `DEBUG` | Mode debug (toujours False en prod) | `False` |
| `SECRET_KEY` | Clé secrète Django | Générer avec `python manage.py shell` |
| `DB_PASSWORD` | Mot de passe PostgreSQL | À définir dans `.env` |
| `GOOGLE_OAUTH_CLIENT_ID` | ID client Google | Depuis Google Cloud Console |
| `ALLOWED_HOSTS` | Hôtes autorisés | `localhost,127.0.0.1,web` |

## Dépendances optimisées

✅ **Incluses:**
- Django 5.2.8
- PostgreSQL 16
- Google OAuth (allauth)
- Pillow (traitement images)
- Gunicorn (serveur WSGI)

❌ **Supprimées (inutiles):**
- `django-nested-admin` (dev only)
- `setuptools-scm` (version control only)
- Toutes les dépendances transitives de dev

**Taille image finale:** ~420MB (très léger grâce au multi-stage build)

## Production Tips

### SSL/HTTPS
```yaml
# Ajouter à nginx.conf pour HTTPS
server {
    listen 443 ssl http2;
    ssl_certificate /etc/nginx/certs/cert.pem;
    ssl_certificate_key /etc/nginx/certs/key.pem;
    # ... reste de la config
}
```

### Scaling
```bash
# Augmenter les workers Gunicorn dans docker-compose.yml
command: gunicorn ... --workers 8
```

### Monitoring
```bash
# Voir l'utilisation des ressources
docker stats
```

## Troubleshooting

**Erreur: "Connection refused" PostgreSQL**
```bash
# Vérifier que db est healthy
docker-compose ps
# Réinitialiser la db
docker-compose down -v && docker-compose up -d
```

**Port 8000/80 déjà utilisé**
```bash
# Modifier docker-compose.yml:
# Changer "80:80" à "8080:80"
ports:
  - "8080:80"
```

**Migrations non appliquées**
```bash
docker-compose exec web python manage.py migrate --run-syncdb
```

---

✨ Bon déploiement! Pour des questions, consulte la [doc Django](https://docs.djangoproject.com/) ou [Docker](https://docs.docker.com/)
