import json
import os
import uuid

from litellm.llms.openai import openai

from app.PipelineTask import PipelineTask
from mosaicrs.llm.LiteLLMLLMInterface import LiteLLMLLMInterface

_rag_system_prompt = (
    "You are a helpful conversational assistant using a RAG system. Your goal is to answer "
    "user queries using ONLY the provided documents (separated by <SEP>).\n\n"
    "RULES:\n"
    "1. SOURCE ADHERENCE: Use strictly the provided text. No outside knowledge or assumptions. "
    "If the answer isn't there, say: \"The provided documents do not contain sufficient information.\"\n"
    "2. LANGUAGE: Respond in the SAME language as user talks to you in.\n"
    "3. CONVERSATIONAL STYLE: Maintain a natural, helpful tone. Do not say 'According to the documents' "
    "every sentence. Integrate the facts into a fluid conversation.\n"
    "4. FORMATTING: Use **bolding** for key terms, dates, or technical specs. Use clear paragraphs.\n"
    "5. CITATION: If multiple facts are presented, use brief inline mentions like [Doc 1] if available, "
    "otherwise just synthesize the information.\n"
    "6. GREETINGS: You may respond to greetings (Hi, Hello) naturally, but for any factual "
    "question, refer strictly to the documents."
    "\nThe Documents:"
).strip()



class ConversationTask:
    def __init__(self, model: str, column: str, pipeline_task: PipelineTask):
        self.model = model
        self.column = column
        self.pipeline_task = pipeline_task

        self.uuid = uuid.uuid4().hex

        self.llm = LiteLLMLLMInterface()


        self.messages = []

        # feed with documents
        documents = self.pipeline_task.final_df[self.column].tolist()
        self.add_request(_rag_system_prompt + '<SEP>'.join(documents))


    def add_request(self, message: str) -> str:
        self.messages.append(
            {
                "role": "user",
                "content": message,
            }
        )


        response_string = self.llm.chat(self.model, conversation=self.messages)


        self.messages.append({
            "role": "assistant",
            "content": response_string,
        })

        return response_string





