import json
import os
from typing import List, Dict
import openai

from mosaicrs.llm.LLMInterface import LLMInterface


class LiteLLMLLMInterface(LLMInterface):

    supported_models = json.loads(os.environ.get('LITELLM_MODELS'))

    def __init__(self, system_prompt: str = ''):
        LLMInterface.__init__(self)

        api_key = os.environ.get('LITELLM_APIKEY')
        url = os.environ.get('LITELLM_URL')
        self.client = openai.OpenAI(api_key=api_key, base_url=url)
        self.system_prompt = system_prompt

    def generate(self, prompt: str, model: str):
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": self.system_prompt + prompt},
            ],
            stream=False
        )

        return response.choices[0].message.content

    def chat(self, model: str, conversation: List[Dict[str, str]]) -> str:
        response = self.client.chat.completions.create(
            model=model,
            messages=conversation,
            stream=False
        )

        return response.choices[0].message.content