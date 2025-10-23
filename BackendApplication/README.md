# BackendApplication (Flask)

REST API for managing network devices with MongoDB integration and graceful DB-down handling.

## Endpoints

- GET /health
- GET /api/v1/devices
- POST /api/v1/devices
- GET /api/v1/devices/{id}
- PUT /api/v1/devices/{id}
- DELETE /api/v1/devices/{id}
- GET /api/v1/devices/{id}/status
- GET /openapi.json
- GET /docs

Responses use:
- Success: { "success": true, "data": ... }
- Error: { "success": false, "error": "message" }

## Environment

- PORT (default 3001)
- FLASK_ENV (development|production)
- CORS_ORIGINS (default *)
- MONGODB_URI (e.g., mongodb://mongo:27017/devicesdb) or DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export MONGODB_URI="mongodb://localhost:27017/devicesdb"
# Dev server (Flask)
python app.py
# Or run via Gunicorn using the WSGI entrypoint (mirrors container start)
# PORT can be overridden; default is 3001
export PORT=${PORT:-3001}
gunicorn -b 0.0.0.0:${PORT} wsgi:create_app()
```

## Troubleshooting

- Database unavailable: API returns 503 with { success: false, error }. /health still returns success with db_available=false.
- Duplicate IP: POST/PUT returns 409 "Device with this IP already exists".
- Ping unavailable: status will return offline if ping fails or is blocked.
