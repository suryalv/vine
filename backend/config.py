import os

# ─── LLM Backend ────────────────────────────────────────────────
# Options: "gemini", "bedrock", "openai"
LLM_BACKEND = os.getenv("LLM_BACKEND", "gemini")

# ─── Embedding Backend ──────────────────────────────────────────
# Options: "gemini", "bedrock", "openai"
EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "gemini")

# ─── Gemini ───────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.0-flash")
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "models/gemini-embedding-001")

# ─── AWS Bedrock ─────────────────────────────────────────────────
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
BEDROCK_CHAT_MODEL = os.getenv("BEDROCK_CHAT_MODEL", "anthropic.claude-3-sonnet-20240229-v1:0")
BEDROCK_EMBED_MODEL = os.getenv("BEDROCK_EMBED_MODEL", "amazon.titan-embed-text-v2:0")

# ─── OpenAI ──────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-large")

# ─── Embedding ───────────────────────────────────────────────────
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "3072"))

# ─── Vector Store Backend ────────────────────────────────────────
# Options: "lancedb", "pgvector", "mongodb_atlas"
VECTOR_STORE_BACKEND = os.getenv("VECTOR_STORE_BACKEND", "lancedb")

# LanceDB settings (used when VECTOR_STORE_BACKEND = "lancedb")
LANCE_DB_PATH = os.getenv("LANCE_DB_PATH", "/tmp/uw_companion_lancedb")
LANCE_TABLE_NAME = os.getenv("LANCE_TABLE_NAME", "document_chunks")

# PgVector settings (used when VECTOR_STORE_BACKEND = "pgvector")
PGVECTOR_CONNECTION_STRING = os.getenv(
    "PGVECTOR_CONNECTION_STRING",
    "postgresql://localhost:5432/uw_companion",
)

# MongoDB Atlas settings (used when VECTOR_STORE_BACKEND = "mongodb_atlas")
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "uw_companion")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "document_chunks")

# ─── RAG ──────────────────────────────────────────────────────────
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "64"))
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "8"))

# ─── Hallucination Detection ────────────────────────────────────
HALLUCINATION_WEIGHTS = {
    "retrieval_confidence": 0.25,
    "response_grounding": 0.35,
    "numerical_fidelity": 0.20,
    "entity_consistency": 0.20,
}

# Scalable hallucination settings
MAX_GROUNDING_CHUNKS = int(os.getenv("MAX_GROUNDING_CHUNKS", "20"))
GROUNDING_THRESHOLD = float(os.getenv("GROUNDING_THRESHOLD", "0.65"))
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "50"))
VOLUME_THRESHOLD = int(os.getenv("VOLUME_THRESHOLD", "50"))
HALLUCINATION_VOLUME_WEIGHTS = {
    "retrieval_confidence": 0.30,
    "response_grounding": 0.30,
    "numerical_fidelity": 0.20,
    "entity_consistency": 0.20,
}

# ─── API ─────────────────────────────────────────────────────────
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:4200,http://127.0.0.1:4200",
).split(",")
