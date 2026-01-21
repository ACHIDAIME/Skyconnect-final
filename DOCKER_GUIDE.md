# 🐳 SKYCONNECT Docker Setup Guide

## Prérequis
- Docker Desktop installé ([https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop))
- 4GB RAM minimum alloué à Docker
- Clés Google OAuth (voir `.env.example`)

## Installation & Démarrage

### 1️⃣ Configuration initiale
```bash
# Cloner le repository
git clone https://github.com/ACHIDAIME/Skyconnect-final.git
cd Skyconnect-final

# Copier le fichier d'exemple
cp .env.example .env

# Éditer .env avec tes paramètres
# ⚠️ IMPORTANT en production:
#   - DJANGO_SECRET_KEY: nouvelle clé sécurisée
#   - DB_PASSWORD: mot de passe PostgreSQL sécurisé
#   - GOOGLE_OAUTH_CLIENT_ID et SECRET: depuis Google Cloud Console
#   - EMAIL_HOST_USER et PASSWORD: App Password Gmail
#   - ALLOWED_HOSTS: ton domaine (exemple: monsite.com,www.monsite.com)
nano .env
```

### 2️⃣ Construire et démarrer les conteneurs
```bash
# Build l'image Docker
docker-compose build

# Démarrer les services (migration + chargement fixture + démarrage)
docker-compose up -d
```

**La commande de démarrage fait:**
1. ✅ Applique les migrations
2. ✅ Charge la fixture (tous tes données)
3. ✅ Collecte les fichiers statiques
4. ✅ Lance Gunicorn


### 3️⃣ Initialiser la base de données
```bash
# Les migrations + fixture se chargent automatiquement au démarrage
# Mais si tu veux charger manuellement:

# Appliquer les migrations
docker-compose exec web python manage.py migrate

# Charger la fixture (tous tes données)
docker-compose exec web python manage.py loaddata fixtures/initial_data.json

# Créer un superuser admin (optionnel)
docker-compose exec web python manage.py createsuperuser
```

### 4️⃣ Accéder à l'application
- **Frontend:** http://localhost:8080
- **Admin Django:** http://localhost:8080/admin/
- **API (si applicable):** http://localhost:8080/api/

## 📦 Gestion des données (Fixtures)

### Qu'est-ce qu'une fixture?
Une **fixture** est un fichier JSON contenant TOUTES les données de la base de données:
- ✅ Logos
- ✅ Produits
- ✅ Catégories & Sous-catégories
- ✅ Offres/Forfaits
- ✅ Tickets WiFi
- ✅ Commandes
- ✅ Utilisateurs
- ✅ Configurations (pages, FAQ, etc.)
- ✅ **TOUT!**

### Ajouter/Modifier des données
Quand tu ajoutes un produit, une offre, un ticket, etc. en admin local, il faut **exporter une nouvelle fixture**:

```bash
# Exporter les données actualisées
docker-compose exec web python manage.py dumpdata --all --indent 2 --output=/tmp/data.json

# Copier la fixture du Docker vers le repo local
docker cp skyconnect_app:/tmp/data.json fixtures/initial_data.json

# Committer et pousser
git add fixtures/initial_data.json
git commit -m "data: update fixture with new products/offers/tickets/etc"
git push
```

**Après ce push**, quand quelqu'un d'autre clone le repo et lance Docker, il aura **TOUTES** ces données!

### Workflow pour ajout de contenu
1. Ajouter en admin local (logo, produit, offre, ticket, etc.)
2. Exporter la fixture
3. Commit + push
4. ✅ Le serveur aura tout à jour!

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

## 🚀 Déploiement sur serveur de production

### Checklist avant de donner l'image
- ✅ Tous tes produits, offres, tickets ajoutés en admin
- ✅ Fixture exportée et pushée: `docker-compose exec web python manage.py dumpdata --all --output=/tmp/data.json`
- ✅ `.env.example` complété avec les variables
- ✅ Tout commité et pushé sur GitHub

### Pour quelqu'un qui reçoit l'image
```bash
# 1. Cloner
git clone https://github.com/ACHIDAIME/Skyconnect-final.git
cd Skyconnect-final

# 2. Configurer .env
cp .env.example .env
nano .env  # Remplir avec les vraies variables de production

# 3. Déployer
docker-compose build
docker-compose up -d
```

**C'est tout!** ✨
- Toutes tes données (produits, offres, tickets, logos) sont chargées automatiquement
- Les fichiers media vont dans les volumes (sauvegarde séparée si besoin)

---

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
