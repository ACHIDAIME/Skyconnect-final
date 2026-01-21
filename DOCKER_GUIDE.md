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
Une **fixture** est un fichier JSON contenant **ABSOLUMENT TOUTES** les données de la base de données:

**Contenus éditoriaux:**
- ✅ Logos
- ✅ Sliders
- ✅ Actualités
- ✅ QuickBlocks

**Produits & Offres:**
- ✅ Produits
- ✅ Catégories & Sous-catégories
- ✅ Forfaits/Offres
- ✅ Tickets WiFi

**Configuration:**
- ✅ **Zones de couverture**
- ✅ **FAQ & FAQ Steps**
- ✅ Agences
- ✅ Messages de contact

**Utilisateurs & Commandes:**
- ✅ Utilisateurs
- ✅ Commandes
- ✅ Paniers
- ✅ Demandes de souscription

**En bref:** Tout ce que tu ajoutes via Django admin est automatiquement dans la fixture! 🎯

### Ajouter/Modifier des données
Quand tu ajoutes **N'IMPORTE QUOI** en admin local (logo, produit, offre, ticket, zone de couverture, FAQ, etc.), il faut **exporter une nouvelle fixture**:

⚠️ **ATTENTION:** Si tu n'exporte PAS la fixture, tes données resteront SEULEMENT sur ta machine locale! Le serveur ne verra rien!

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
1. Ajouter du contenu en admin local (n'importe quoi: logos, produits, offres, tickets, zones, FAQ, etc.)
2. Exporter la fixture
3. Commit + push
4. ✅ Le serveur aura TOUT à jour!

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

### ⚠️ Checklist PRÉ-DÉPLOIEMENT (CRITIQUE)

Avant d'aller en ligne, tu DOIS faire ceci:

#### 1. Exporter la fixture complète
```bash
docker-compose exec web python manage.py dumpdata --all --output=/tmp/final_data.json
docker cp skyconnect_app:/tmp/final_data.json fixtures/initial_data.json
git add fixtures/initial_data.json
git commit -m "data: final fixture for production"
git push
```

#### 2. Générer une clé Django sécurisée
```bash
docker-compose exec web python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
➜ Copie cette clé, tu en auras besoin dans le `.env` du serveur

#### 3. Préparer le `.env` de production
```bash
# GÉNÉRER une clé SÉCURISÉE (voir étape 2)
DJANGO_SECRET_KEY=PASTE_THE_KEY_HERE

# CHANGER le mot de passe PostgreSQL
DB_PASSWORD=UN_MOT_DE_PASSE_TRÈS_SÉCURISÉ_32_CARACTÈRES

# REMPLACER par ton VRAI domaine
ALLOWED_HOSTS=monsite.com,www.monsite.com

# CONFIGURER Google OAuth
GOOGLE_OAUTH_CLIENT_ID=TON_ID_GOOGLE
GOOGLE_OAUTH_CLIENT_SECRET=TON_SECRET_GOOGLE
GOOGLE_OAUTH_REDIRECT_URI=https://monsite.com/accounts/google/login/callback/

# CONFIGURER Email (Gmail App Password)
EMAIL_HOST_USER=noreply@monsite.com
EMAIL_HOST_PASSWORD=TON_APP_PASSWORD_GMAIL

# IMPORTANT: DEBUG DOIT ÊTRE FALSE!
DEBUG=False
```

#### 4. Activer HTTPS/SSL
Utiliser **Let's Encrypt** (gratuit):
```bash
# Sur le serveur, installer Certbot
sudo apt-get install certbot python3-certbot-nginx

# Générer le certificat
sudo certbot certonly --standalone -d monsite.com -d www.monsite.com

# Certs seront dans: /etc/letsencrypt/live/monsite.com/
```

Ajouter au `nginx.conf`:
```nginx
server {
    listen 443 ssl http2;
    server_name monsite.com www.monsite.com;
    
    ssl_certificate /etc/letsencrypt/live/monsite.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/monsite.com/privkey.pem;
    
    # Reste de la config...
}

# Redirection HTTP -> HTTPS
server {
    listen 80;
    server_name monsite.com www.monsite.com;
    return 301 https://$server_name$request_uri;
}
```

#### 5. Volumes persistants sur le serveur
```bash
# Créer les dossiers de données
sudo mkdir -p /data/postgres
sudo mkdir -p /data/media
sudo mkdir -p /data/backups

# Donner les permissions
sudo chown 999:999 /data/postgres  # Pour PostgreSQL
sudo chown 1000:1000 /data/media   # Pour Django
```

#### 6. Backup automatique (cron job)
```bash
#!/bin/bash
# Créer /home/user/backup.sh

docker-compose exec -T db pg_dump -U skyconnect skyconnect | \
  gzip > /data/backups/db_$(date +%Y%m%d_%H%M%S).sql.gz

tar -czf /data/backups/media_$(date +%Y%m%d_%H%M%S).tar.gz /data/media

# Ajouter à crontab (backup tous les jours à 2h du matin):
# crontab -e
0 2 * * * cd /home/user/skyconnect && bash backup.sh
```

---

### 📋 Étapes de déploiement sur le serveur

```bash
# 1. Sur le SERVEUR, cloner le repo
git clone https://github.com/ACHIDAIME/Skyconnect-final.git
cd Skyconnect-final

# 2. Copier et configurer .env
cp .env.example .env
nano .env  # ⚠️ REMPLACER TOUTES les variables (voir checklist au-dessus)

# 3. Déployer
docker-compose build
docker-compose up -d

# 4. Vérifier que tout fonctionne
docker-compose ps  # Les 3 services doivent être "Up"
docker-compose logs web  # Vérifier pas d'erreurs

# 5. Accéder au site
https://monsite.com  ✅
```

---

### 🔒 Sécurité - À NE PAS oublier

- ✅ `DEBUG=False` obligatoirement
- ✅ `DJANGO_SECRET_KEY` nouvelle clé aléatoire
- ✅ `DB_PASSWORD` mot de passe fort (32+ caractères)
- ✅ `ALLOWED_HOSTS` = ton domaine exactement
- ✅ HTTPS/SSL activé (Let's Encrypt gratuit)
- ✅ Backups automatiques configurés
- ✅ Ne JAMAIS mettre le `.env` en Git (il y a un `.gitignore`)

---

### 📊 Monitoring en production

```bash
# Voir l'utilisation des ressources
docker stats

# Voir les logs en temps réel
docker-compose logs -f web

# Backup manuel de la DB
docker-compose exec db pg_dump -U skyconnect skyconnect > backup_manual.sql

# Vérifier la santé des conteneurs
docker-compose ps
```

---

### 🆘 Troubleshooting en production

```bash
# Redémarrer l'app
docker-compose restart web

# Redémarrer tout
docker-compose restart

# Voir les erreurs détaillées
docker-compose logs web
docker-compose logs db

# Vérifier que PostgreSQL est healthy
docker-compose exec db pg_isready -U skyconnect
```

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
