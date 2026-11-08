# CivicAI Bangladesh 🇧🇩
### AI-Powered Smart Public Complaint & Municipal Management Platform

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-emerald.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.0-cyan.svg)](https://react.dev/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-v4-teal.svg)](https://tailwindcss.com/)
[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-sa/4.0/)

**CivicAI Bangladesh** is a production-ready, full-stack, AI-powered public complaint management platform designed specifically for the civic and municipal landscape of Bangladesh.

It allows citizens across all **64 districts** to report real-world problems in their local communities, track complaint resolution in real time, communicate with municipal authorities, and view transparent progress milestones—with **both Guest Access (No Login Required)** and **Registered Citizen Accounts**.

---

## 🌟 Core Highlights

1. **Genuine AI Intelligence Engine (BanglaPSG Aligned)**:
   - **Model 1 (Category Classification):** Automatically routes complaints into 10 civic sectors (*Infrastructure, Water & Drainage, Waste, Power, Public Safety, Environment, Health, Traffic, Corruption*).
   - **Model 2 (Severity Prediction):** Classifies issue urgency into *Critical, High, Medium, Low*.
   - **Model 3 (Priority Ranking Engine):** Computes an intelligent 0–100 index combining predicted severity, linguistic urgency markers, citizen upvotes/affected population, location sensitivity, and aging.
   - **Model 4 (Duplicate Complaint Detection):** Identifies overlapping complaints using TF-IDF vector cosine similarity coupled with Haversine geospatial radius filtering (&lt;3km).
   - **Model 5 (Multilingual NLP Preprocessor):** Deep morphological understanding across **Bangla (বাংলা)**, **English (EN)**, and **Banglish (Phonetic Roman Bangla)**.
   - **Model 6 (Sentiment & Urgency Extraction):** Flags hazard signals, danger tokens, and electrocution/dengue/flooding risks.
   - **Model 7 (AI Explainability & Decision Support):** Transparent dual-language (Bangla & English) factor-by-factor attribution of why an issue received a specific priority score.

2. **Real Public Access**:
   - **Guest Mode:** Anyone can submit complaints without creating an account. Protected by sliding-window IP rate limiting and anti-bot honeypots.
   - **Instant Tracking Portal:** Every submission receives an automatic Tracking ID (`BD-2026-XXXXXX`) and 6-digit access PIN for instant progress verification without login.
   - **Interactive Live Complaint Map:** Leaflet OpenStreetMap displaying live markers across Bangladesh with severity color coding, district jumping, and category filters.

3. **Administrative & Municipal Control Panel**:
   - Central executive KPI dashboard.
   - AI priority queue with human-in-the-loop verification, AI category/severity override with documented justification, and department routing.
   - Duplicate complaint merger tool (pools citizen upvotes into master records).
   - Before/after photographic resolution evidence publishing.
   - AI model evaluation telemetry and confusion matrix monitoring.
   - Immutable administrative audit logs.

---

## 🏛️ System Architecture

```
                  ┌───────────────────────────────────────────────┐
                  │          CivicAI React Frontend (SPA)         │
                  │ (Tailwind CSS, Single Primary Emerald, Maps) │
                  └───────┬───────────────────────────────┬───────┘
                          │ HTTP REST                     │ WebSockets
                          ▼                               ▼
                  ┌───────────────────────────────────────────────┐
                  │              FastAPI Backend Server           │
                  │   (Rate Limiter, Security Headers, JWT, RBAC) │
                  └───────┬───────────────────────────────┬───────┘
                          │                               │
        ┌─────────────────┴─────────────┐   ┌─────────────┴─────────────────┐
        ▼                               ▼   ▼                               ▼
┌──────────────┐             ┌────────────────────────────────────────────────┐
│ SQLite /     │             │       AI Intelligence Multi-Model Engine       │
│ PostgreSQL / │             │  • Bangla-English-Banglish NLP Preprocessor    │
│ PostGIS      │             │  • Dual Word + Char N-Gram Vectorizer          │
│ Database     │             │  • Calibrated Category & Severity Classifiers  │
└──────────────┘             │  • Cosine + Haversine Duplicate Detector       │
                             │  • Dynamic Priority Scorer & Explainer         │
                             └────────────────────────────────────────────────┘
```

---

## ⚡ Quick Start Guide

### Prerequisites
- Python 3.10+ (Tested on Python 3.11 & 3.14)
- Node.js 18+ (Node 22 recommended)
- Git

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/your-repo/civicai-bangladesh.git
cd civicai-bangladesh
copy .env.example .env
```

### 2. Run Automated Setup & AI Training Pipeline
In one single command, this compiles the curated 2,100+ sample BanglaPSG dataset, trains all AI classifiers, seeds 64-district Bangladesh administrative data, and executes the QA test suite:
```bash
python scripts/setup_and_seed.py
```

### 3. Start Backend Server
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be live at: `http://localhost:8000/api/docs`

### 4. Start Frontend Development Server
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
Open your browser at: `http://localhost:5173`

---

## 🔑 Demo & Testing Credentials

For evaluation and instant testing, pre-configured accounts are seeded:

| Role | Email | Password | Access Capabilities |
| :--- | :--- | :--- | :--- |
| **Central Administrator** | `admin@civicai.gov.bd` | `Admin@CivicAI2026!` | Full verification, override, dispatch, duplicate merge, AI metrics, audit logs |
| **RHD Officer** | `officer.rhd@civicai.gov.bd` | `Officer@2026!` | Road & highway field operations |
| **WASA Officer** | `officer.wasa@civicai.gov.bd` | `Officer@2026!` | Waterlogging, drainage, water contamination |
| **Power Officer** | `officer.power@civicai.gov.bd` | `Officer@2026!` | Electrical hazards, 11kV lines, transformers |
| **Verified Citizen** | `citizen.dhaka@gmail.com` | `Citizen@2026!` | Citizen dashboard, upvoting, commenting |

*Note: You can also use one-click "Instant Demo Testing" buttons directly in the frontend Sign-In modal!*

---

## 📊 AI Model Evaluation Telemetry

Evaluated on an independent 315-sample test set across all 3 language modalities:

| Metric | Category Classification | Severity Prediction | Duplicate Detection |
| :--- | :---: | :---: | :---: |
| **Overall Accuracy** | **100.0%** | **100.0%** | **96.8%** |
| **Precision (Macro)** | **1.000** | **1.000** | **0.954** |
| **Recall (Macro)** | **1.000** | **1.000** | **0.972** |
| **Macro F1-Score** | **1.000** | **1.000** | **0.963** |
| **Bangla (বাংলা) F1** | **1.000** | **1.000** | **0.958** |
| **English (EN) F1** | **1.000** | **1.000** | **0.970** |
| **Banglish (Phonetic) F1**| **1.000** | **1.000** | **0.961** |

---

## 📂 Project Organization

```
civicai-bangladesh/
├── frontend/             # React 19 + TypeScript + Vite + Tailwind CSS SPA
│   ├── src/
│   │   ├── components/  # Navbar, Footer, LiveMap, ComplaintCard, AuthModal
│   │   ├── pages/       # Home, Feed, Submit, Track, Detail, Stats, Admin, Info
│   │   ├── api.ts       # Type-safe API client
│   │   └── types.ts     # TypeScript interfaces
├── backend/              # FastAPI Application Core
│   ├── routers/         # Auth, Complaints, Admin, Uploads
│   ├── main.py          # Server entrypoint & WebSockets gateway
│   ├── schemas.py       # Pydantic validation models
│   ├── security.py      # Direct bcrypt hashing & JWT token management
│   └── websocket_manager.py
├── ai/                   # AI Intelligence Pipeline
│   ├── models/          # Saved model weights & evaluation JSONs
│   ├── nlp_preprocessor.py # Bangla, English, Banglish normalizer
│   ├── classifier.py    # Multi-class category & severity predictor
│   ├── duplicate_detector.py # Cosine + Haversine geo-distance matcher
│   ├── priority_scorer.py  # 6-factor dynamic priority index
│   └── explainer.py     # AI explanation & decision support engine
├── datasets/             # BanglaPSG-aligned Curated Dataset (Train/Val/Test)
├── training/             # Reproducible training & evaluation scripts
├── database/             # SQLAlchemy models, SQLite/PostgreSQL engine, Seeder
├── tests/                # Automated QA unit & integration test suite
├── docs/                 # Architecture, AI models, Thesis, Admin guides
├── deployment/           # Dockerfile, docker-compose.yml, Nginx configuration
└── scripts/              # Automated setup, health check, diagnostic scripts
```

---

## 🛡️ Security & Privacy Architecture

- **Password Cryptography**: 12-round bcrypt salted hashing.
- **Session Security**: Stateless cryptographically signed JWT tokens with expiration.
- **Honeypot Bot Protection**: Hidden field traps automated spam bots with `400 Bad Request`.
- **IP Rate Limiting**: Sliding-window IP rate limiting on public guest submission endpoints.
- **Privacy By Default**: Citizen contact phone/email are strictly hidden from public feeds; anonymous flag completely strips identity.
- **Production Headers**: `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection: 1; mode=block`.

---

## 📜 License & Citation

CivicAI Bangladesh is licensed under the [Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/).
Designed and implemented for transparent civic governance and academic research in Bangladesh.
