# Backend - Salla Autonomous Merchant Operations

Multi-agent system built with LangGraph for autonomous merchant operations.

## Architecture

### Agents

1. **Coordinator Agent** (`nodes.py:coordinator_node`)
   - Initializes workflow
   - Dispatches to parallel workers
   - Tracks execution state

2. **Catalog Agent** (`agents/catalog_agent.py`)
   - Normalizes product data
   - Detects duplicates and inconsistencies
   - Validates data quality

3. **Support Agent** (`agents/support_agent.py`)
   - Classifies customer messages
   - Analyzes sentiment trends
   - Detects complaint spikes

4. **Pricing Agent** (`agents/pricing_agent.py`)
   - Generates pricing proposals
   - Applies business rules
   - Explains decisions

5. **Resolver** (`nodes.py:conflict_resolver_node`)
   - Cross-validates agent outputs
   - Applies merchant locks
   - Generates final report

6. **Throttler** (`nodes.py:throttler_node`)
   - Safety circuit breaker
   - Freezes operations on anomalies

### State Management

The `AgentState` (in `state.py`) is the shared blackboard:
- Raw data inputs
- Agent outputs
- System flags
- Final report

### Workflow Graph

```
Coordinator → Support → Catalog → Safety Gate
                                      ↓
                              ┌───────┴────────┐
                              ↓                ↓
                          Throttler        Pricing
                              ↓                ↓
                              └───────┬────────┘
                                      ↓
                                  Resolver
```

## Running Locally

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

**Option A: OpenAI**
```bash
# Windows
set LLM_PROVIDER=openai
set OPENAI_API_KEY=your_key
set LANGCHAIN_TRACING_V2=true
set LANGCHAIN_API_KEY=your_langsmith_key

# Mac/Linux
export LLM_PROVIDER=openai
export OPENAI_API_KEY=your_key
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=your_langsmith_key
```

**Option B: Azure OpenAI**
```bash
# Windows
set LLM_PROVIDER=azure
set AZURE_OPENAI_API_KEY=your_azure_key
set AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
set AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini

# Mac/Linux
export LLM_PROVIDER=azure
export AZURE_OPENAI_API_KEY=your_azure_key
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
export AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
```

See `../docs/AZURE_OPENAI_SETUP.md` for detailed Azure setup.

### 3. Test the Graph

```bash
python run_test.py
```

### 4. Run the API Server

```bash
uvicorn main:app --reload
```

API will be available at http://localhost:8000

## API Endpoints

- `GET /` - API info
- `GET /health` - Health check
- `POST /api/run` - Run operations check
- `GET /api/status` - System status
- `GET /docs` - Interactive API documentation

## Key Files

- `graph.py` - LangGraph workflow definition
- `state.py` - Shared state schema
- `nodes.py` - Orchestration nodes
- `agents/` - Individual agent implementations
- `main.py` - FastAPI application
- `data_loader.py` - Sample data loader

## LangSmith Integration

Traces are automatically sent to LangSmith when:
- `LANGCHAIN_TRACING_V2=true`
- `LANGCHAIN_API_KEY` is set

View traces at: https://smith.langchain.com/

## Safety Features

1. **Complaint Spike Detection**
   - Monitors complaint velocity
   - Triggers throttler if spike detected
   - Freezes all pricing changes

2. **Sentiment Gate**
   - Blocks price increases when sentiment < 0
   - Protects brand during negative feedback

3. **Cost Floor**
   - Prevents pricing below cost
   - Maintains minimum 5% margin

4. **Merchant Locks**
   - Respects manual overrides
   - Immutable merchant decisions

5. **Cross-Agent Validation**
   - Resolver checks for contradictions
   - Flags hallucinations
   - Applies fallback logic

## Development

### Adding a New Agent

1. Create file in `agents/your_agent.py`
2. Define agent function with state parameter
3. Return dict with state updates
4. Add to `agents/__init__.py`
5. Add node to `graph.py`
6. Connect edges in workflow

### Modifying Business Rules

Edit the logic in:
- `agents/pricing_agent.py` - Pricing rules
- `nodes.py:conflict_resolver_node` - Resolution logic

### Testing

```bash
# Run test script
python run_test.py

# Run with custom data
python -c "from graph import app; print(app.invoke({...}))"
```
