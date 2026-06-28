# Deployment Guide

This guide details how to deploy the SysAi assistant to a production environment.

---

## 💻 1. Frontend Production Build

The frontend is bootstrapped with Vite. To package it for production:

1. **Compile Static Assets**:
   ```bash
   cd frontend
   npm run build
   ```
   This will bundle all React component logic, Tailwind classes, and assets into a highly compressed static folder `frontend/dist/`.

2. **Serve Static Assets**:
   You can serve `frontend/dist/` using any standard web server like **Nginx**, **Apache**, or **Caddy**.
   *Nginx Server Block Example*:
   ```nginx
   server {
       listen 80;
       server_name productivity.local;

       location / {
           root /var/www/sysai/frontend/dist;
           index index.html;
           try_files $uri $uri/ /index.html;
       }

       location /api {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

---

## 🐍 2. Backend Production Run (FastAPI)

In production, avoid running FastAPI with uvicorn's `--reload` flag. Instead, use a production-ready WSGI/ASGI runner like **Gunicorn** or multiple Uvicorn worker threads:

```bash
cd backend
# Run with 4 concurrent worker processes
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
```

### Systemd Service Configuration
On Linux servers, keep the backend active using a systemd service:
Create `/etc/systemd/system/sysai-backend.service`:
```ini
[Unit]
Description=SysAi Assistant Backend Service
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/sysai/backend
ExecStart=/var/www/sysai/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always

[Install]
WantedBy=multi-user.target
```
Enable and start the service:
```bash
sudo systemctl enable --now sysai-backend
```

---

## 🐳 3. Containerized Deployment (Docker)

To run the entire suite under Docker, we provide standard Docker configurations.

### `Dockerfile` (Backend)
Create a file `backend/Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install build essentials for Vosk/soundfile if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `Dockerfile` (Frontend)
Create a file `frontend/Dockerfile`:
```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install --legacy-peer-deps
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Using these containers, you can ship the application instantly to cloud VPS instances or local Kubernetes setups.
