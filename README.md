# uOttawa Brightspace LLM Assistant

An AI-powered assistant that helps uOttawa students interact with their Brightspace courses through natural language queries.

## Features

- 🤖 AI-powered course assistance using Mistral LLM
- 📚 Access course content, assignments, and grades
- 🔐 Secure integration with uOttawa SSO
- 📱 Responsive web interface
- 🔄 Real-time data synchronization with Brightspace

## Quick Start

1. **Clone and setup:**
   ```bash
   git clone <your-repo-url>
   cd uottawa-brightspace-assistant
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start with Docker:**
   ```bash
   docker-compose up -d
   ```

3. **Or run locally:**
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload

   # Frontend (new terminal)
   cd frontend
   npm install
   npm run dev
   ```

## Documentation

- [Setup Guide](docs/SETUP.md)
- [API Documentation](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Brightspace Integration](docs/BRIGHTSPACE_INTEGRATION.md)

## Project Structure

```
├── backend/           # FastAPI backend
├── frontend/          # React frontend
├── data-pipeline/     # Data extraction and processing
├── infrastructure/    # Docker, K8s, Terraform
└── docs/             # Documentation
```

## License

MIT License - University of Ottawa
