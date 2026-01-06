import os
import uuid

from litellm.llms.openai import openai

from app.PipelineTask import PipelineTask


_rag_system_prompt = (
    "You are an AI assistant in a Retrieval-Augmented Generation (RAG) system. Your purpose is to answer questions strictly "
    "and exclusively based on the content provided in the retrieved documents. Follow these guidelines:\n\n"
    "1. Use Provided Information Only:\n"
    "   - Only use the content from the provided documents to generate responses.\n"
    "   - Do not rely on prior knowledge, external sources, or assumptions.\n\n"
    "2. Acknowledge Gaps:\n"
    "   - If the provided documents do not contain sufficient information to answer a question, clearly state that the information is not available.\n"
    "   - Avoid making inferences beyond the explicit content in the documents.\n\n"
    "3. Precision and Fidelity:\n"
    "   - Ensure your answers remain faithful to the source material, accurately reflecting its content and context.\n"
    "   - Quote or reference document excerpts when relevant to support your answers.\n\n"
    "4. No Speculation or Fabrication:\n"
    "   - Do not generate content that isn't directly supported by the documents.\n"
    "   - Avoid filling in gaps with plausible but unverified information.\n\n"
    "5. Clarity and Neutrality:\n"
    "   - Present the information clearly and objectively.\n"
    "   - Do not introduce personal opinions, interpretations, or bias.\n\n"
    "Failure Mode:\n"
    "If no relevant information is found in the provided documents, respond with:\n"
    "\"The provided documents do not contain sufficient information to answer this question.\"\n\n"
    "The documents will be provided at the end of this prompt, separated by <SEP>."
)



class ConversationTask:
    def __init__(self, model: str, column: str, pipeline_task: PipelineTask):
        self.model = model
        self.column = column
        self.pipeline_task = pipeline_task

        self.uuid = uuid.uuid4().hex

        # with open('innkube.apikey', 'r') as file:
        #     api_key = file.read().rstrip()

        api_key = os.environ.get('INNKUBE_APIKEY')

        self.client = openai.OpenAI(api_key=api_key, base_url='https://llms-inference.innkube.fim.uni-passau.de')

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

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            stream=False
        )

        response_string = response.choices[0].message.content

        self.messages.append({
            "role": "assistant",
            "content": response_string,
        })

        return response_string





