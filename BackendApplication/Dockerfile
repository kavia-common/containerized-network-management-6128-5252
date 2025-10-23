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
# Default command to start Flask app using Gunicorn binding to 0.0.0.0:3001
# Uses the wsgi:create_app() factory to avoid importing the package named "app" incorrectly.
CMD ["gunicorn", "-w", "2", "-k", "gthread", "--threads", "4", "-b", "0.0.0.0:3001", "--timeout", "60", "--graceful-timeout", "30", "--access-logfile", "-", "--error-logfile", "-", "wsgi:create_app"]
