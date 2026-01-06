import os
from typing import List, Dict, Optional

from openai import OpenAI

from mosaicrs.llm.LLMInterface import LLMInterface

class DeepSeekLLMInterface(LLMInterface):

    def __init__(self, system_prompt: str = 'You are a helpful assistant'):
        LLMInterface.__init__(self)

        # with open('deepseek.apikey', 'r') as file:
        #     api_key = file.read().rstrip()

        api_key = os.environ.get('DEEPSEEK_APIKEY')

        self.system_prompt = system_prompt
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    def generate(self, prompt: str):
        response = self.client.chat.completions.create(
            model='deepseek-reasoner',
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": "Summarize: " + prompt},
            ],
            stream=False
        )

        return response.choices[0].message.content


    def chat(self, conversation: List[Dict[str, str]]) -> str:
        pass

