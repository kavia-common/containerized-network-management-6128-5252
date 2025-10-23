# Python slim image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y iputils-ping && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 3001

ENV PORT=3001
# Use a dedicated WSGI entrypoint to avoid module/package name conflicts.
# Bind explicitly to 0.0.0.0 and the configured PORT.
CMD ["gunicorn", "-b", "0.0.0.0:3001", "wsgi:create_app()"]
