# Aura-AI — 3-Tier Emotional Wellness & Voice Companion

Aura AI is a production-grade, multi-agent AI therapeutic companion built with a modern 3-tier architecture. It combines real-time voice and text chat, multi-agent cognitive orchestration (using LangGraph and Google Gemini), and dynamic mood tracking and analytics.

---

## 🏛️ System Architecture Overview

```text
+-----------------------------------------------------------------------------------+
|                              TIER 1: FRONTEND LAYER                               |
|                     (React 19 + Vite + Tailwind CSS + Vanilla JS)                 |
|                                                                                   |
|  [VoiceChat.jsx] <---> [Vite Proxy (/api/*)] <---> [Dashboard.jsx / Analytics]    |
+-----------------------------------------------------------------------------------+
                                        |
                                        v  HTTP / REST JSON
+-----------------------------------------------------------------------------------+
|                              TIER 2: BACKEND LAYER                                |
|                        (Python FastAPI + SQLite Asyncio)                          |
|                                                                                   |
|  [main.py Lifespan] --> Initializes app.state.ai_app & DB Connection              |
|  [api/chat.py]      --> Receives /api/chat/ -> Streams/invokes LangGraph pipeline |
|  [api/auth.py]      --> JWT / Admin Bypass Authentication                         |
+-----------------------------------------------------------------------------------+
                                        |
                                        v  State & Context Passing
+-----------------------------------------------------------------------------------+
|                             TIER 3: AI CORE LAYER                                 |
|               (LangGraph Multi-Agent Orchestration + Google Gemini)               |
| [safety_node]      ---> Screens incoming input for risk/crisis content            |
| [supervisor_entry] ---> Evaluates intent & routes to specialized agents:           |
|      ├── [emotion_node]       --> Classifies emotional state (joy, sadness, etc.) |
|      ├── [memory_agent]       --> Reads/writes user context from SQLite Checkpoints|
|      ├── [rag_node]           --> Retrieves therapeutic knowledge (FAISS / CPU)   |
|      └── [wellness_plan_node] --> Generates actionable psychological advice       |
|  [synthesis_node]   ---> Weaves outputs into empathetic, human-centric response   |
+-----------------------------------------------------------------------------------+
```

---

## 📂 Repository Directory Structure

```text
Aura-AI/
├── .gitignore                   # Git tracking exclusion rules
├── index.html                   # Single Page Application entry HTML
├── package-lock.json           # Locked Node.js dependency tree
├── package.json                # Frontend dependencies and build scripts
├── postcss.config.js           # PostCSS setup for Tailwind CSS
├── README.md                    # Project overview & documentation
├── render.yaml                  # Backend deployment setup (Render)
├── requirements.txt            # Backend & AI core Python packages
├── tailwind.config.js          # Tailwind styling rules
├── vercel.json                  # Frontend deployment setup (Vercel)
├── vite.config.js              # Vite build setup & dev server proxy
│
├── ai_core/                     # TIER 3: LangGraph AI Pipeline & Multi-Agent Engine
│   ├── agents/                  # Autonomous agent nodes (supervisor, emotion, memory, rag, wellness_plan, safety)
│   ├── graph/                   # LangGraph state machine builder, checkpointer, and edge definitions
│   ├── llm/                     # Groq API client instances and Llama model tier configurations
│   ├── prompts/                 # System prompts for agent routing, sentiment, safety, and wellness plans
│   ├── rag/                     # Vector store pipeline, mental health document PDFs, embeddings, & preprocessors
│   ├── runtime/                 # App lifecycle setup, execution entrypoints, and async streaming
│   ├── scripts/                 # Embeddings creation and document ingestion execution scripts
│   ├── state/                   # Shared state schemas and reducer functions for LangGraph execution
│   ├── tests/                   # Integration and unit test suite for the AI pipeline
│   └── utils/                   # Telemetry, metrics collection, and application loggers
│
├── backend/                     # TIER 2: FastAPI Web Server & Database Infrastructure
│   ├── api/                     # REST API routers (chat, auth, history, journal, mood, rag, users, voice, wellness)
│   ├── database/                # Async SQLAlchemy connection setup, CRUD handlers, ORM models, and schemas
│   ├── middleware/              # Authentication & session verification middleware
│   ├── utils/                   # Server logging utilities
│   ├── voice/                   # Audio handling, Speech-to-Text, and Text-to-Speech utilities
│   ├── config.py                # Pydantic Settings & environment variable configuration
│   └── main.py                  # FastAPI application entrypoint & app lifecycle state setup
│
├── src/                          # TIER 1: React Single Page Application (Frontend)
│   ├── assets/                  # Graphics, icons, and hero media
│   ├── components/              # Reusable UI elements (Navigation, AudioPlayer, MoodGraph)
│   ├── pages/                   # Route views (Dashboard.jsx, Login.jsx, Settings.jsx, VoiceChat.jsx)
│   ├── utils/                   # Client-side helpers and local storage wrappers
│   ├── App.css                  # Main application component layout styles
│   ├── App.jsx                  # Main React router and client root component
│   ├── config.js                # Frontend API base URL configuration
│   ├── index.css                # Global Tailwind CSS directives
│   └── main.jsx                 # DOM mounting entrypoint file
│
├── docs/                         # Project Documentation & Historical Artifacts
│   ├── legacy_archive/          # Historical code iterations and archived extractions
│   ├── HOW_TO_RUN.md            # Developer quickstart and execution instructions
│   └── PROJECT_OVERVIEW.md      # Architectural specifications and system design notes
│
├── public/                       # Public static assets (favicons, SVG icon sprites)
│
└── scripts/                      # Database & System Maintenance Tools
    ├── reset_database.py        # Wipes and resets local database tables
    ├── setup_db.py              # Seeds initial database schema and tables
    ├── test_pipeline.py         # Diagnostic runner for LangGraph pipeline testing
    └── verify_faiss.py          # Validates vector database index health
```

---
## 👥 Contributors

Aura AI was built by a team of five as part of a GenAI & Agentic AI internship capstone.

| Member | Module | Agent Ownership |
|---|---|---|
| **Somaansh** | Frontend + Dashboard | Emotion Agent |
| **Bhumi Kharb** | LangGraph + Orchestration | Supervisor Agent + Memory Agent |
| **Aditi** | RAG Pipeline | Knowledge Retrieval Agent |
| **Sheel** | Backend + Voice + Database | Voice Integration (major feature, not a standalone agent) |
| **Bhumi Saxena** | Safety + Mood Tracker + Wellness Plan + Testing + Deployment | Safety Agent |
'''

---

## 🚀 How to Run Locally

### 1. Prerequisites
- **Node.js** (v18 or higher)
- **Python** (3.10 to 3.14 compatible)
- **Google Gemini API Key** (Get one free from [Google AI Studio](https://aistudio.google.com/))

### 2. Environment Configuration (`.env`)
Ensure your `.env` file exists in the project root with your valid API key:
```env
GROQ_API_KEY=your_groq_api_key

Aura_ENV=development
DATABASE_URL=sqlite+aiosqlite:///./wellness_companion.db
FRONTEND_URL=http://localhost:5173
```

### 3. Start the Backend Server (Terminal 1)
Open a terminal in the project root and launch FastAPI with live reloading:
```powershell
uvicorn backend.main:app --reload
```
*The server will initialize the SQLite database, compile the LangGraph AI pipeline, and listen on **http://localhost:8000**.*

### 4. Start the Frontend Dev Server (Terminal 2)
Open a second terminal window and launch Vite:
```powershell
npm run dev
```
*The frontend dev server will launch on **http://localhost:5173** and proxy all `/api/*` requests directly to `http://localhost:8000/api/*`.*

---

## 🔬 Engineering & Troubleshooting Notes

1. **Python 3.14 Compatibility:** We use `PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1` during builds to allow `pydantic-core` and C-extension libraries to compile cleanly across newer Python runtimes.
2. **AI Rate Limits & Auto-Retry:** `ai_core/llm/clients.py` configures `GeminiChatModel` with `max_retries=4` and uses `gemini-2.5-flash` (`ai_core/llm/models.py`) to prevent quota exhaustion and automatically back off on rate-limit spikes (`429 RESOURCE_EXHAUSTED`).
3. **Pydantic Settings Configuration:** `backend/config.py` uses `"extra": "ignore"` inside `Settings.model_config` to ensure that adding new environment variables to `.env` will never cause validation failures during application startup.
4. **Testing the AI Pipeline:** To verify AI core connectivity without booting the full web stack, run the standalone diagnostic tool:
```powershell
   python scripts/test_pipeline.py
```

---

