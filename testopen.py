import openai
from dotenv import load_dotenv
load_dotenv()  # By default, loads .env from current working dir

client = openai.OpenAI(api_key="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")

try:
    result = client.embeddings.create(input=["Hello world!"], model="text-embedding-ada-002")
    print("Result:", result)
except Exception as e:
    print("Error:", e)
