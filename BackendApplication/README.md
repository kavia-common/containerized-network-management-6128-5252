# BackendApplication (Flask)

Flask REST API with MongoDB integration.

Run locally
- python3 -m venv .venv && source .venv/bin/activate
- pip install -r requirements.txt
- export SERVER_HOST=0.0.0.0 SERVER_PORT=3001 API_PREFIX=/api/v1 MONGODB_URI=mongodb://localhost:27017 MONGODB_DB=devicesdb LOG_LEVEL=INFO
- python app.py

Endpoints
- GET /health
- GET {API_PREFIX}/openapi.json
- GET {API_PREFIX}/docs
- CRUD under {API_PREFIX}/devices
- GET {API_PREFIX}/devices/{id}/status

DB Unavailability
- When MongoDB is down, database-dependent endpoints return 503 with a clear message.
- /health and docs remain available.

Indexes
- Unique index on devices.ip_address
- Indexes on type and status

Troubleshooting
- Duplicate IP: 400 error from POST/PUT.
- Connection refused: verify MONGODB_URI and DB container is running.
- OpenAPI not loading: ensure pyyaml installed and file present.

Docker
- See Dockerfile in this folder.

Docker Compose (example)
- Add a backend service like:
  backend:
    build: ./BackendApplication
    container_name: backend
    environment:
      - SERVER_HOST=0.0.0.0
      - SERVER_PORT=3001
      - API_PREFIX=/api/v1
      - MONGODB_URI=mongodb://mongo:27017
      - MONGODB_DB=devicesdb
      - LOG_LEVEL=INFO
    ports:
      - "3001:3001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3001/health"]
      interval: 10s
      timeout: 3s
      retries: 5
      start_period: 5s
    depends_on:
      - mongo

- The container listens on 0.0.0.0:3001 and responds to:
  - GET / -> {"success": true, "service": "backend", "message": "OK"}
  - GET /health -> includes db_available flag
