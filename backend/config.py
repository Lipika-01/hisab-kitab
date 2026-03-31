import os

MONGO_URI = os.environ.get("MONGO_URI")
DB_NAME = os.environ.get("DB_NAME", "hisabkitab")

if not MONGO_URI:
    raise ValueError("MONGO_URI is not set")