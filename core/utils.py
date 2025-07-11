import openai

def get_embedding(text, model="text-embedding-ada-002"):
    emb = openai.embeddings.create(input=[text], model=model)
    return emb.data[0].embedding