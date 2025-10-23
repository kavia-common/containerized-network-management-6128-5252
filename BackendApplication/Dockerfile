# Backend Flask Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3001

# PUBLIC_INTERFACE
# Default command to start Flask app (gunicorn could be added later)
CMD ["python", "app.py"]
