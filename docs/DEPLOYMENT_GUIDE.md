# CivicAI Bangladesh - Production Deployment Guide

## 1. Production Architecture Overview

The system can be deployed in two recommended production topologies:

### Topology A: Unified Containerized Docker Deployment
Ideal for VPS, DigitalOcean Droplet, AWS EC2, or dedicated server.
```bash
cd deployment
docker compose up -d --build
```
This automatically initializes:
- PostgreSQL 15 + PostGIS container
- FastAPI Python 3.11 Backend container
- Nginx Reverse Proxy container (Port 80/443)

---

### Topology B: Serverless Cloud Deployment (Vercel + Render / Hugging Face + Supabase)

#### 1. Database (Neon or Supabase PostgreSQL)
1. Create a free PostgreSQL instance on [Neon](https://neon.tech) or [Supabase](https://supabase.com).
2. Copy the Connection URI into `.env`:
   ```env
   DATABASE_URL=postgresql://user:password@ep-host.region.neon.tech/civicai_bd?sslmode=require
   ```

#### 2. Backend (Render / Railway / Hugging Face Spaces)
1. Push repository to GitHub.
2. Connect repository to [Render](https://render.com) or [Railway](https://railway.app).
3. Set Build Command:
   ```bash
   pip install -r backend/requirements.txt && python scripts/setup_and_seed.py
   ```
4. Set Start Command:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```
5. Configure Environment Variables (`SECRET_KEY`, `ENVIRONMENT=production`, `DATABASE_URL`, `CORS_ORIGINS`).

#### 3. Frontend (Vercel / Cloudflare Pages)
1. Connect frontend folder to [Vercel](https://vercel.com).
2. Set Root Directory: `frontend`
3. Set Framework Preset: `Vite`
4. Set Environment Variable:
   ```env
   VITE_API_URL=https://your-backend-api.onrender.com
   ```
5. Deploy!
