# Resume Grader – RAG-Based Resume & Job Description Analyzer
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6F00?style=flat)
![React](https://img.shields.io/badge/React-61DAFB?style=flat&logo=react&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)

Resume Grader is a full-stack RAG (Retrieval-Augmented Generation) application that compares an uploaded resume against a job description and returns a structured, requirement-by-requirement gap analysis. It was built from scratch as a portfolio project to explore embedding-based semantic matching, RAG pipeline design, and secure document handling end-to-end.

**Live Demo**: [https://your-deployment-url.vercel.app]

---

## Running with Docker

**Prerequisites:** [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)

```bash
git clone https://github.com/your-username/resume-grader.git
cd resume-grader
# Create a .env file with your DB credentials, JWT secret, and Gemini API key
docker compose up --build
```

App runs at **http://localhost:8080**.

```bash
docker compose down          # stop
docker compose down -v       # stop and wipe the database
```

---

## Running Locally (Without Docker)

### Prerequisites
- Python 3.11+
- Node.js (for the React frontend)
- A running PostgreSQL instance

```bash
git clone https://github.com/your-username/resume-grader.git
cd resume-grader
pip install -r app/requirements.txt
alembic upgrade head
```

Copy and fill in the `.env` file (see above), then point `DB_HOST` at your local PostgreSQL host (e.g. `localhost`).

```bash
uvicorn app.main:app --reload
```

Backend runs at **http://localhost:8080** (or the configured `$PORT`).

---

## Environment Variables

Create a `.env` file in the project root (this file is gitignored — never commit real secrets):

```bash
# Database
DB_HOST=localhost
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_PORT=5432
DB_NAME=resume_db

# Auth
JWT_KEY=your_jwt_secret_key
JWT_ALG=HS256

# Storage paths
FILE_PATH=/absolute/path/to/app/disk_stor/
CHROMA_PATH=/absolute/path/to/app/chroma_db

# LLM
GEMINI_API_KEY=your_gemini_api_key
```

`FILE_PATH` and `CHROMA_PATH` should be absolute paths on the machine/container running the backend — in Docker these typically point at `/app/disk_stor/` and `/app/chroma_db` per the Dockerfile's `mkdir`.

---

## Key Features

### Resume & Job Description Upload
- PDF resume upload with strict file validation (magic bytes, size cap, page count, encryption check)
- JD submission as plain text, with input sanitization against injection and malicious payloads
- Per-analysis `job_id` scoping so resume and JD data never mix across sessions

### RAG-Based Gap Analysis
- Resumes and job descriptions are parsed, header-classified, and chunked into labeled sections (skills, experience, education, projects / requirements, optional, responsibilities)
- Chunks are embedded with `all-MiniLM-L6-v2` (sentence-transformers) and stored in per-job ChromaDB collections
- Each JD requirement is matched against the closest resume chunks using cosine similarity
- Matches are bucketed into **covered**, **partial**, and **gap** based on tuned similarity thresholds

### AI-Generated Feedback
- Structured match/gap data is assembled into a prompt and sent to an LLM (Gemini)
- Feedback is streamed to the client in real time and covers: overall assessment, strong matches, missing/weak areas, resume language & impact, targeted rewording suggestions, and interview risk areas

### Authentication & Job Tracking
- JWT-based session authentication (`OAuth2PasswordBearer`)
- Bcrypt password hashing with enforced complexity rules
- Ownership checks per job via a PostgreSQL `jobs` table (Alembic-managed migrations)

## Technology Stack

### Backend
- **FastAPI** – REST API, request validation, streaming responses (SSE)
- **PostgreSQL + SQLAlchemy** – Relational storage for users and job records
- **Alembic** – Database migrations
- **ChromaDB** – Vector storage for resume and JD embeddings, scoped per `job_id`
- **sentence-transformers (`all-MiniLM-L6-v2`)** – Text embedding for semantic matching
- **PyMuPDF / pymupdf4llm** – PDF parsing, markdown conversion, and sanitization
- **Google Gemini API** – LLM-generated feedback, streamed via SSE

### Authentication & Security
- JWT-based authentication with expiring access tokens
- Bcrypt password hashing with enforced complexity rules
- PDF validation: magic-byte check, 5MB size cap, page count cap, encryption rejection, embedded script/JS scrubbing
- JD text validation against prompt-injection and code-injection patterns (shell commands, SQL, script tags, path traversal)
- Parameterized queries via SQLAlchemy ORM

**Note:** Security mechanisms are implemented for educational purposes and are not intended for production financial or hiring systems.

### Frontend
- React (Login, UploadResume, UploadJobDescription, Results components)
- Server-Sent Events (SSE) consumption for streamed analysis results

### Deployment
- **Frontend** – Vercel
- **Backend** – Railway (containerized via Docker)
- **Database** – Neon (managed PostgreSQL)
- Alembic migrations run manually at deploy time

## API Overview

### Authentication
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

### Analysis
- `POST /analyze/upload_resume`
- `POST /analyze/upload/job_description`
- `POST /analyze/analyze/{job_id}` — streams the gap analysis and feedback as SSE

## Database Design

- **Users** – Authentication and profile data
- **Jobs** – Per-analysis job records (`job_id`, `user_id`, `status`) used for ownership checks and progress tracking

## RAG Pipeline (Backend Deep Dive)

1. Resume PDF is validated, converted to markdown, and split into labeled chunks
2. JD text is validated, then split by header keywords into requirements / optional / responsibilities sections
3. Both sets of chunks are embedded and stored in isolated ChromaDB collections (`resume_{job_id}`, `jd_{job_id}`)
4. Each JD requirement chunk is queried against the resume collection to find its closest matches
5. Matches are scored and bucketed (covered / partial / gap) using similarity-distance thresholds
6. The structured gap summary is turned into a prompt and streamed through an LLM for human-readable feedback
7. ChromaDB collections for the job are deleted once analysis completes

## Project Purpose

This project demonstrates:
- RAG pipeline design: chunking, embedding, vector search, and threshold-based classification
- RESTful API design with FastAPI, including SSE streaming
- Secure file handling for untrusted PDF uploads
- Prompt engineering for structured, requirement-level LLM feedback
- JWT-based authentication and per-resource ownership checks
- Full-stack integration with a React frontend
- Cloud deployment across separate frontend, backend, and database providers

## Known Limitations
- ChromaDB runs in-memory within the backend process (not a standalone persistent service)
- Synchronous analysis pipeline — no background job queue
- Similarity thresholds were manually tuned rather than learned/validated against a labeled dataset

## Future Improvements
- Automated `.md` file and ChromaDB cleanup with deterministic filenames
- Background job queue (e.g. Redis-based) for longer-running analyses
- Automated pytest test suite and CI/CD pipeline
- OCR fallback for scanned/image-based resumes