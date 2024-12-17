from typing import Optional, List, Dict

from transformers import T5Tokenizer, T5ForConditionalGeneration

from mosaicrs.llm.LLMInterface import LLMInterface

class T5Transformer(LLMInterface):
    def __init__(self, model: str, system_prompt: Optional[str] = None):
        super().__init__(model, system_prompt)

        self.tokenizer = T5Tokenizer.from_pretrained(self.model)
        self.model = T5ForConditionalGeneration.from_pretrained(self.model)



    def generate(self, prompt: str):
        input_ids = self.tokenizer.encode(
            prompt, return_tensors="pt", max_length=512, truncation=True
        )
        output_ids = self.model.generate(input_ids, max_length=150, num_beams=4, early_stopping=True)
        response = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)

        return response

    def chat(self, conversation: List[Dict[str, str]]) -> str:
        pass