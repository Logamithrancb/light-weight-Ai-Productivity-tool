import os

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Database configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "personal_productivity")
SQLITE_PATH = os.path.join(BASE_DIR, "backend", "productivity.db")

# Models configuration
SAVED_MODELS_DIR = os.path.join(BASE_DIR, "ml", "saved_models")

# Vosk Offline Speech Recognition
VOSK_MODEL_DIR = os.path.join(BASE_DIR, "backend", "vosk_model")
VOSK_MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"

# App Port
PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "127.0.0.1")
