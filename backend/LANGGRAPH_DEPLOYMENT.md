# LangGraph Official Deployment Pattern

This application now uses the **official LangGraph deployment pattern** instead of a custom FastAPI wrapper.

## What Changed

### Before (Custom FastAPI Wrapper - NOT RECOMMENDED)
```python
# main.py - Custom wrapper
app = FastAPI(...)
@app.post("/api/run")
async def run_operations(...):
    result = langgraph_app.invoke(initial_state)
```

### After (Official LangGraph Pattern - CORRECT)
```json
// langgraph.json - Official configuration
{
  "dependencies": ["."],
  "graphs": {
    "salla_ops": "./graph.py:app"
  },
  "env": ".env"
}
```

## Architecture Changes

### 1. Self-Sufficient Coordinator Node
The `coordinator_node` in `nodes.py` now loads its own data if not provided:
- Checks if `product_data` exists in state
- If missing, loads sample data automatically
- Makes the graph independent of external data injection

### 2. LangGraph Configuration
Created `langgraph.json` that defines:
- Graph location: `./graph.py:app`
- Graph name: `salla_ops`
- Environment file: `.env`

### 3. Official API Endpoints
The LangGraph CLI automatically provides:
- `POST /runs/stream` - Stream graph execution
- `POST /runs/invoke` - Synchronous execution
- `GET /runs/{run_id}` - Get run status
- Standard LangGraph/LangServe protocol

### 4. Updated Frontend Integration
Frontend now uses the standard LangGraph streaming API:
```typescript
fetch(`${apiUrl}/runs/stream`, {
  method: 'POST',
  body: JSON.stringify({
    assistant_id: "salla_ops",
    input: { merchant_id: merchantId },
    stream_mode: "values"
  })
})
```

## Running the Application

### Development (Local)
```bash
cd backend
langgraph dev --host 0.0.0.0 --port 8000
```

### Production (Docker)
```bash
docker compose -f docker-compose.local.yml up --build
```

The Dockerfile now uses:
```dockerfile
CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "8000"]
```

## Benefits

1. **Framework Compliance**: Uses official LangGraph deployment pattern
2. **Ecosystem Integration**: Compatible with LangSmith, LangServe, and other LangChain tools
3. **Standard Endpoints**: Auto-generated REST API following LangGraph conventions
4. **Better Monitoring**: Native integration with LangSmith tracing
5. **Production Ready**: Official deployment path for LangGraph applications

## API Endpoints

### Stream Execution (Recommended)
```bash
POST /runs/stream
Content-Type: application/json

{
  "assistant_id": "salla_ops",
  "input": {
    "merchant_id": "merchant_001"
  },
  "stream_mode": "values"
}
```

### Synchronous Execution
```bash
POST /runs/invoke
Content-Type: application/json

{
  "assistant_id": "salla_ops",
  "input": {
    "merchant_id": "merchant_001"
  }
}
```

## Migration Notes

- The old `main.py` has been renamed to `main.py.backup` for reference
- All custom FastAPI endpoints have been replaced with standard LangGraph endpoints
- The frontend has been updated to use the streaming API
- Data loading is now handled internally by the coordinator node

## LangSmith Integration

The application automatically integrates with LangSmith when configured:
```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_key_here
LANGCHAIN_PROJECT=salla-ops-system
```

All graph executions are automatically traced and visible in the LangSmith dashboard.
