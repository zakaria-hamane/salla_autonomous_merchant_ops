FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy application code
COPY . .

# Set dummy env for build (will be overridden at runtime)
ENV AZURE_OPENAI_API_KEY=dummy-key-for-build
ENV AZURE_OPENAI_ENDPOINT=https://dummy.openai.azure.com
ENV AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5
ENV AZURE_OPENAI_API_VERSION=2025-04-01-preview
ENV NEXT_PUBLIC_API_URL=http://localhost:8000

# Build the application
RUN npm run build

# Expose port
EXPOSE 3000

# Run the application
CMD ["npm", "start"]
