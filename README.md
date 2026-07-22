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
|                                                                                   |
|  [supervisor_entry] ---> Evaluates intent & routes to specialized agents:         |
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
mindmate-ai/
├── ai_core/                    # TIER 3: LangGraph AI Pipeline & Agents
│   ├── agents/                 # Agent Nodes: supervisor, emotion, memory, rag, wellness_plan
│   ├── graph/                  # LangGraph StateDefinition & Graph Compilation (builder.py)
│   ├── llm/                    # Gemini API clients, model tier definitions (2.5-flash), prompts
│   ├── rag/                    # FAISS vector store and document processing
│   └── runtime/                # Lifecycle management (build_app) & async streaming execution
│
├── backend/                    # TIER 2: FastAPI Gateway & Database Models
│   ├── api/                    # REST API endpoints (chat.py, auth.py, voice.py, wellness.py)
│   ├── database/               # Async SQLAlchemy database connection & schema initialization
│   ├── models/                 # ORM Models (User, ChatMessage, MoodLog, WellnessPlan)
│   ├── config.py               # Pydantic Settings & environment variable configuration
│   └── main.py                 # FastAPI application entrypoint & app.state lifecycle
│
├── src/                        # TIER 1: Frontend Web Application
│   ├── components/             # Reusable UI components (Navigation, AudioPlayer, MoodGraph)
│   ├── pages/                  # Route views (Dashboard.jsx, VoiceChat.jsx, Settings.jsx)
│   └── utils/                  # Client-side helpers and local storage wrappers
│
├── docs/                       # Project Documentation & Historical Archives
│   ├── HOW_TO_RUN.md           # Quickstart installation and running guide
│   ├── PROJECT_OVERVIEW.md     # Original architectural specifications
│   └── legacy_archive/         # Archive of initial module extractions
│
├── scripts/                    # Utility & Maintenance Scripts
│   ├── setup_db.py             # Script to initialize database tables manually
│   ├── reset_database.py       # Script to wipe and reseed database tables
│   └── test_pipeline.py        # Standalone diagnostic script for testing LangGraph execution
│
├── public/                     # Static web assets (icons, favicon)
├── requirements.txt            # Python dependencies (FastAPI, LangGraph, LangChain, FAISS)
├── package.json                # Node.js dependencies (React, Vite, Tailwind CSS)
├── vite.config.js              # Vite bundler & backend API reverse proxy configuration
└── .env                        # Environment configuration and secrets (not tracked in Git)
```

---

## 🚀 How to Run Locally

### 1. Prerequisites
- **Node.js** (v18 or higher)
- **Python** (3.10 to 3.14 compatible)
- **Google Gemini API Key** (Get one free from [Google AI Studio](https://aistudio.google.com/))

### 2. Environment Configuration (`.env`)
Ensure your `.env` file exists in the project root with your valid API key:
```env
GOOGLE_API_KEY=your_actual_google_gemini_api_key
HOMEMIND_ENV=development
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
