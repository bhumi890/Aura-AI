"""
ai_core/config.py

Centralized environment + tuning configuration. Keep thresholds and
environment switches here so they never require touching agent code.
"""
import os

# -- Environment --------------------------------------------------------
ENV = os.getenv("HOMEMIND_ENV", "development")  # "development" | "production"

# -- Checkpointing --------------------------------------------------------
POSTGRES_CONN_STRING = os.getenv("POSTGRES_CONN_STRING", "")
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "homemind_dev.db")

# -- Memory agent tuning --------------------------------------------------
# Only re-summarize long-term memory every N turns, not every single turn.
SUMMARIZE_TRIGGER_TURNS = int(os.getenv("SUMMARIZE_TRIGGER_TURNS", "8"))
MEMORY_SUMMARY_MAX_WORDS = 200

# -- Chat history windowing ------------------------------------------------
# How many recent messages to feed into each LLM call (not the full history).
ENTRY_HISTORY_WINDOW = 6
FINAL_HISTORY_WINDOW = 10

# -- RAG ------------------------------------------------------------------
RAG_TOP_K = 3

# -- Model names (see llm/models.py for the constants actually imported) --
# NOTE: gemini-2.5-flash / gemini-2.5-flash-lite are mid-deprecation on
# Google's side (early 404s ahead of their official Oct 2026 shutdown) --
# see llm/clients.py for details. FAST_MODEL points at a current, GA,
# non-deprecated model instead of a soon-to-be-retired one.
FAST_MODEL = "gemini-3.5-flash"
SYNTHESIS_MODEL = "gemini-3.5-flash"
