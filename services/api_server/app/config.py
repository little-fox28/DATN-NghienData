"""
backend/config.py — Configuration for Backend FastAPI Service
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Server Settings
HOST = os.getenv("BACKEND_HOST", "127.0.0.1")
PORT = int(os.getenv("BACKEND_PORT", 8000))
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Database Connection (from .env)
DB_SERVER = os.getenv("DB_SERVER", "localhost")
DB_NAME = os.getenv("DB_NAME", "CreditRiskDB")
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
