import uuid

from litellm.llms.openai import openai

from app.PipelineTask import PipelineTask


class ConversationTask:

    def __init__(self, model: str, column: str, pipeline_task: PipelineTask):
        self.model = model
        self.column = column
        self.pipeline_task = pipeline_task

        self.uuid = uuid.uuid4().hex

        with open('innkube.apikey', 'r') as file:
            api_key = file.read().rstrip()

        self.client = openai.OpenAI(api_key=api_key, base_url='https://llms-inference.innkube.fim.uni-passau.de')

        self.messages = []


        # feed with documents
        documents = self.pipeline_task.final_df[self.column].tolist()
        first_message = 'You are part of a helpful RAG system named MosaicRAG. You will be given a list of documents, separated by <SEP>. Answer the users questions based on these documents alone.\n' + '<SEP>'.join(documents)
        self.add_request(first_message)


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





