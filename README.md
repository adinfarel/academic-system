# Academic-System 🎓

> Integrated Academic System based on Computer Vision & AI Agent for the Polsri campus environment.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

---

## Description

PolsriEduAI is a modern academic platform that combines:

- **Face Recognition + Liveness Detection** — real-time automatic attendance without the ability to spoof photos
- **AI Academic Agent** — a RAG (Retrieval-Augmented Generation)-based assistant that answers academic questions contextually and personally
- **Integrated Dashboard** — a single platform for students, lecturers, and administrators
- **JWT Authentication** — a system token-based secure authentication

---

## Tech Stack

| Layers | Technology |
|---|---|
| Frontend | HTML5, CSS3, Vanilla JS |
| Backend | Python 3.11+, FastAPI |
| Databases | PostgreSQL + SQLAlchemy ORM |
| AI/RAG | Groq API (LLaMA), ChromaDB (Vector DB) |
| CV | OpenCV, face_recognition / DeepFace |
| Auth | JWT (python-jose) |
| Migration | Alembic |

---

## Project Structure

polsri-edu-ai/
│
├── README.md
├── .gitignore
├── requirements.txt
│
├── frontend/
│   ├── assets/
│   │   ├── css/
│   │   │   ├── base.css
│   │   │   ├── components.css
│   │   │   └── layout.css
│   │   └── js/
│   │       ├── api.js
│   │       ├── auth.js
│   │       └── utils.js
│   ├── pages/
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── admin/
│   │   │   └── dashboard.html
│   │   ├── dosen/
│   │   │   └── dashboard.html
│   │   └── mahasiswa/
│   │       ├── dashboard.html
│   │       ├── absensi.html
│   │       └── ai-assistant.html
│   └── components/
│
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   │   ├── mahasiswa.py
│   │   ├── dosen.py
│   │   ├── absensi.py
│   │   └── user.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── absensi.py
│   │   ├── akademik.py
│   │   └── ai_agent.py
│   ├── services/
│   │   ├── face_recognition.py
│   │   ├── liveness.py
│   │   └── ai_agent.py
│   ├── rag/
│   │   ├── indexer.py
│   │   ├── retriever.py
│   │   └── groq_client.py
│   ├── data/
│   │   └── pedoman_akademik/
│   └── migrations/
│
└── docs/
└── README.md

---

## Cara Menjalankan (Development)

### 1. Clone repo
```bash
git clone https://github.com/adinfarel/polsri-edu-ai.git
cd polsri-edu-ai
```

### 2. Setup virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup environment variables
```bash
cp .env.example .env
# Edit .env sesuai konfigurasi lokal kamu
```

### 5. Jalankan database migration
```bash
alembic upgrade head
```

### 6. Jalankan backend
```bash
uvicorn backend.main:app --reload
```

---

## Roadmap

- [x] Fase 0 — Setup project & GitHub
- [ ] Fase 1 — Frontend statis (Landing, Login, Dashboard)
- [ ] Fase 2 — Backend fondasi (Auth, Models, API)
- [ ] Fase 3 — Computer Vision & Absensi
- [ ] Fase 4 — AI Agent & RAG

---

## 👨‍💻 Author

**adinfarel** — [@adinfarel](https://github.com/adinfarel)
