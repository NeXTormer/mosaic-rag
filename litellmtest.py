import requests

response = requests.post(
    f"https://ollama.felixholz.com/v1/embeddings",
    auth=('ollama', '5NuRHQ9Ta7A4CMRag3P6m3'),
    json={
        "model": "text-embedding-jina",
        "input": 'werner'  # Note: Change 'prompt' to 'input' for OpenAI compatibility
    },
    headers={'Content-Type': 'application/json'}
)

print(response)
print(response.json()["data"][0]["embedding"])