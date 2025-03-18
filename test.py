from litellm import completion
import os

## set ENV variables

response = completion(
  model="openai/gemma2",
  api_base='https://llms-inference.innkube.fim.uni-passau.de/',
  api_key=os.environ["OPENAI_API_KEY"],
  messages=[{ "content": "Hello, how are you?","role": "user"}]
)

print(response)

