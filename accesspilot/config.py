"""Runtime settings, read from environment variables (see .env.example)."""
import os

# Gemini model used by every agent. On Vertex AI / Gemini Enterprise Agent Platform
# set GOOGLE_GENAI_USE_VERTEXAI=TRUE plus GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION.
MODEL = os.getenv("ACCESSPILOT_MODEL", "gemini-2.5-flash")

# "sqlite" (default, offline, zero setup) or "alloydb".
DB_BACKEND = os.getenv("ACCESSPILOT_DB", "sqlite").lower()
SQLITE_PATH = os.getenv("ACCESSPILOT_SQLITE_PATH", ":memory:")

# AlloyDB connection string, e.g. through the AlloyDB Auth Proxy:
# postgresql://postgres:<password>@127.0.0.1:5432/accesspilot
ALLOYDB_DSN = os.getenv("ALLOYDB_DSN", "")
# Vertex AI embedding model called from inside AlloyDB (google_ml_integration).
ALLOYDB_EMBEDDING_MODEL = os.getenv("ALLOYDB_EMBEDDING_MODEL", "text-embedding-005")

# ServiceNow: leave SERVICENOW_INSTANCE empty to use the in-memory mock.
SERVICENOW_INSTANCE = os.getenv("SERVICENOW_INSTANCE", "")
SERVICENOW_USER = os.getenv("SERVICENOW_USER", "")
SERVICENOW_PASSWORD = os.getenv("SERVICENOW_PASSWORD", "")

# Policy thresholds (USD).
AUTO_APPROVE_MAX_COST = float(os.getenv("AUTO_APPROVE_MAX_COST", "500"))
