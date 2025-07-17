import os
from dotenv import load_dotenv

load_dotenv()

def load_config():
    """Return all relevant config as a dict."""
    return {
        "NEO4J_URI": os.getenv("NEO4J_URI"),
        "NEO4J_USER": os.getenv("NEO4J_USER"),
        "NEO4J_PASS": os.getenv("NEO4J_PASS"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "JWT_SECRET": os.getenv("JWT_SECRET"),
        # ...add more as needed
    }
