from dotenv import load_dotenv
import os

load_dotenv()  # This loads .env contents into os.environ

from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Are you working?"}]
)

print(response.choices[0].message.content)
