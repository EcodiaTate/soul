import os
from dotenv import load_dotenv

load_dotenv()

# Neo4j
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASS = os.getenv("NEO4J_PASS")

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Any other keys go here...
