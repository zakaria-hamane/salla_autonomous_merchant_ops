FROM python:3.11-slim

WORKDIR /app

# Install dependencies including langgraph-cli
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the standard LangGraph port
EXPOSE 8000

# STARTUP COMMAND CHANGED:
# We use the langgraph executable to serve the app defined in langgraph.json
CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "8000"]
