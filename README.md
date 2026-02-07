# Salla Autonomous Merchant Operations Multi-Agent System

A multi-agent system for autonomous merchant operations management using LangGraph, LangSmith, and CopilotKit.

## Project Structure

```
.
├── backend/              # LangGraph application & agents
├── frontend/             # Next.js + CopilotKit UI
├── data/                 # Sample datasets
├── docs/                 # Documentation & assignment
├── docker-compose.local.yml
└── .env.example
```

## Quick Start

1. **Setup Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   # Choose OpenAI or Azure OpenAI (see docs/AZURE_OPENAI_SETUP.md)
   ```

2. **Run with Docker Compose**
   ```bash
   docker-compose -f docker-compose.local.yml up --build
   ```

3. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

## Development

### Backend (Python/LangGraph)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```

## Architecture

The system implements a "Gated Pipeline" topology with:
- **Coordinator Agent**: Orchestrates the workflow
- **Catalog Agent**: Normalizes product data
- **Support Agent**: Analyzes customer messages
- **Pricing Agent**: Recommends pricing adjustments
- **Safety Gates**: Circuit breakers for anomaly detection

See `docs/my_plan.md` for detailed architecture.

## Assignment Details

See `docs/Autonomous_Merchant_Operations_Multi_Agent_System.md` for full requirements.

**Deadline**: EOD Tuesday, February 10th, 2026
