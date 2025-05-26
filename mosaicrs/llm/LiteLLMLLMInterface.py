from typing import List, Dict
import openai

from mosaicrs.llm.LLMInterface import LLMInterface


class LiteLLMLLMInterface(LLMInterface):

    supported_models = ["gemma2", "qwen2.5", "llama3.1"]

    def __init__(self, system_prompt='', model='gemma2'):
        LLMInterface.__init__(self)

        with open('innkube.apikey', 'r') as file:
            api_key = file.read().rstrip()

        self.system_prompt = system_prompt
        self.model = '' + model
        self.client = openai.OpenAI(api_key=api_key, base_url='https://llms-inference.innkube.fim.uni-passau.de')


    def generate(self, prompt: str):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )

        return response.choices[0].message.content

    def chat(self, conversation: List[Dict[str, str]]) -> str:
        pass