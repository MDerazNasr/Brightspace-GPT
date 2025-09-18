# Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

## Development Setup

### 1. Environment Configuration

1. Copy environment template:
   ```bash
   cp .env.example .env
   ```

2. Fill in required values:
   - Brightspace API credentials (contact uOttawa IT)
   - Mistral API key
   - uOttawa SSO configuration
   - JWT secret key

### 2. Database Setup

```bash
# Start databases
docker-compose up -d db redis qdrant

# Run migrations
cd backend
alembic upgrade head
```

### 3. Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 5. Data Pipeline Setup

```bash
cd data-pipeline
python -m pip install -r ../requirements.txt
python scripts/initial_sync.py
```

## Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for production setup instructions.
