"""
ai_core/llm/models.py

Named model constants. Node code should NEVER hardcode a model string
directly -- import from here so a model swap is a one-line change.

Model choice notes (see llm/clients.py for the full explanation):
Google has been retiring Gemini models faster than their published
deprecation dates would suggest -- gemini-2.5-flash and
gemini-2.5-flash-lite started returning 404 "not available" errors in
July 2026, well before their announced Oct 2026 shutdown. Both
constants below point at models that are current, generally available,
and NOT on any deprecation notice as of this writing.
"""

# Cheap / fast model -- used for classification, summarization, routing.
# Runs frequently (every turn for supervisor_entry), so cost/latency matter.
FAST_MODEL = "llama-3.1-8b-instant"

# Larger model -- used only for final synthesis, which runs once per turn
# and needs to weave multiple signals into a coherent, empathetic response.
SYNTHESIS_MODEL = "llama-3.3-70b-versatile"
