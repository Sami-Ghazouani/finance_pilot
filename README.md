# BudgetPilot — gestion des tâches et des montants prévisionnels

Application web pédagogique construite avec Flask, PostgreSQL et Docker Compose. Elle permet de suivre des tâches liées à l'organisation financière personnelle, avec un montant estimé, une catégorie, une priorité et une échéance.


## Fonctionnalités

- Création, modification, changement de statut et suppression de tâches.
- Catégories, priorités, échéances et montants estimés.
- Recherche textuelle et filtres par statut/catégorie.
- Indicateurs : nombre de tâches, tâches terminées et montants encore à prévoir.
- Synthèse des montants par catégorie.
- API JSON `GET /api/tasks` et endpoint de santé `GET /health`.
- Validation des champs et requêtes SQL paramétrées.

## Prérequis

- Docker Desktop récent (Windows/macOS) ou Docker Engine + Docker Compose v2.
- Un navigateur web.

## Démarrage avec Docker

1. Copie le fichier d'exemple :

   ```bash
   cp .env.example .env
   ```

   Sous PowerShell :

   ```powershell
   Copy-Item .env.example .env
   ```

2. Dans `.env`, remplace les valeurs de démonstration par des valeurs locales robustes.
3. Lance l'application :

   ```bash
   docker compose up --build -d
   ```

4. Ouvre `http://localhost:5000`. Vérifie le service avec `http://localhost:5000/health`.

Arrêt :

```bash
docker compose down
```

Pour effacer aussi la base locale (action destructive) :

```bash
docker compose down -v
```

## Lancement local sans Docker

Il faut disposer d'un serveur PostgreSQL accessible. Crée un environnement virtuel puis installe les dépendances :

```bash
python -m venv .venv
# Windows PowerShell : .venv\Scripts\Activate.ps1
# macOS/Linux : source .venv/bin/activate
pip install -r requirements.txt
```

Définis `DB_HOST`, `POSTGRES_DB`, `POSTGRES_USER` et `POSTGRES_PASSWORD` dans l'environnement, puis lance :

```bash
python app.py
```

Pour le lancement local, `DB_HOST` vaut `localhost` par défaut.

## API

- `GET /api/tasks` : renvoie les tâches au format JSON.
- `GET /health` : vérifie que l'application peut joindre PostgreSQL.

## Structure

```text
.
├── app.py
├── templates/
│   ├── base.html
│   └── dashboard.html
├── static/
│   └── style.css
├── Dockerfile
├── compose.yaml
├── requirements.txt
└── .env.example
```


