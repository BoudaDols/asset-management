# Système de Gestion des Actifs Municipaux (SGAM)

Plateforme de gestion des actifs d'infrastructure pour les municipalités. Permet de cataloguer, importer et générer des rapports sur les actifs municipaux (réseaux d'eau, stations de pompage, réservoirs, conduites, etc.) selon une taxonomie hiérarchique normalisée à 8 niveaux.

## Fonctionnalités (V1)

- **Catalogue hiérarchique** — 8 niveaux : Service → Fonction → Sous-fonction → Type d'actif → Actif primaire → Discipline → Actif secondaire → Actif tertiaire
- **Gestion des instances** — CRUD d'actifs physiques avec attributs flexibles (JSONB)
- **Importation Excel** — Import en masse via fichiers .xlsx avec validation et rapport d'erreurs
- **Rapports** — Inventaire filtrable, regroupement par hiérarchie, export Excel/PDF
- **Multi-tenant** — Isolation des données par municipalité

## Stack technique

| Couche | Technologie |
|--------|-------------|
| Backend | Python 3.11 + FastAPI |
| Base de données | PostgreSQL 16 |
| ORM | SQLAlchemy (async) + Alembic |
| Tâches asynchrones | Celery + Redis |
| Frontend | React + TypeScript + Vite + Tailwind CSS |
| Infrastructure | Docker Compose |

## Structure du projet

```
├── backend/
│   ├── app/
│   │   ├── main.py              # Point d'entrée FastAPI
│   │   ├── core/                # Config, DB, schemas, exceptions, validators
│   │   ├── models/              # Modèles SQLAlchemy
│   │   ├── catalog/             # Module catalogue (hiérarchie)
│   │   ├── assets/              # Module instances d'actifs
│   │   ├── imports/             # Module importation Excel
│   │   └── reports/             # Module rapports
│   ├── alembic/                 # Migrations de base de données
│   ├── tests/                   # Tests unitaires et d'intégration
│   ├── pyproject.toml           # Dépendances Python
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/               # Pages (Catalogue, Actifs, Import, Rapports)
│   │   ├── components/          # Composants React
│   │   └── lib/                 # Utilitaires
│   ├── package.json
│   └── Dockerfile
├── docker-compose.dev.yml       # Environnement de développement
├── .env.example                 # Variables d'environnement (template)
└── README.md
```

## Démarrage rapide

### Prérequis

- Docker et Docker Compose
- (Optionnel) Python 3.11+ et Node.js 20+ pour le développement local

### Lancer avec Docker Compose

```bash
# Copier les variables d'environnement
cp .env.example .env

# Démarrer tous les services
docker compose -f docker-compose.dev.yml up --build
```

Services disponibles :
- **API** : http://localhost:8000
- **Documentation API (Swagger)** : http://localhost:8000/docs
- **Documentation API (ReDoc)** : http://localhost:8000/redoc
- **Health check** : http://localhost:8000/api/v1/health
- **Frontend** : http://localhost:5173

### Développement local (sans Docker)

#### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

#### Base de données seule (Docker)

```bash
docker compose -f docker-compose.dev.yml up postgres redis -d
```

## Migrations

```bash
cd backend

# Appliquer les migrations
alembic upgrade head

# Créer une nouvelle migration
alembic revision --autogenerate -m "description"

# Revenir en arrière
alembic downgrade -1
```

## Tests

```bash
cd backend
pytest -v                    # Tous les tests
pytest tests/test_config.py  # Un fichier spécifique
pytest --cov=app             # Avec couverture
```

## Arrêter les services

```bash
# Arrêter les conteneurs
docker compose -f docker-compose.dev.yml down

# Arrêter et supprimer les données (reset complet)
docker compose -f docker-compose.dev.yml down -v
```

## Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|--------|
| `DATABASE_URL` | URL de connexion PostgreSQL | `postgresql+asyncpg://postgres:postgres@localhost:5432/asset_management` |
| `REDIS_URL` | URL de connexion Redis | `redis://localhost:6379/0` |
| `CORS_ORIGINS` | Origines autorisées (JSON array) | `["http://localhost:5173"]` |
| `MAX_UPLOAD_SIZE` | Taille max upload en octets | `52428800` (50 Mo) |
| `BATCH_SIZE` | Lignes par lot d'insertion | `100` |
| `PAGE_SIZE_DEFAULT` | Pagination par défaut | `25` |
| `PAGE_SIZE_MAX` | Pagination maximum | `500` |

## Feuille de route

- **V1** (en cours) — Catalogue, instances, import Excel, rapports, multi-tenant
- **V2** — Authentification JWT, RBAC, journal d'audit, gestion des utilisateurs
- **V3** — Cycle de vie des actifs, maintenance, coûts, intégration GIS

## Licence

Propriétaire — © BImpact
