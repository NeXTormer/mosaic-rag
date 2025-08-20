import regex as re
import mosaicrs.pipeline.PipelineErrorHandling as err

from mosaicrs.llm.LiteLLMLLMInterface import LiteLLMLLMInterface
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.PipelineStep import PipelineStep
from difflib import SequenceMatcher

class RelevanceMarkingStep(PipelineStep):

    def __init__(self, input_column: str, output_column: str, query: str = None, model: str = 'gemma2'):
        """
            Initialize the relevance marking step with input/output columns, an optional custom query, and the LLM model. A pipeline step that uses an LLM to highlight the most relevant passages in a text column based on a given query. Relevant segments are marked by surrounding them with double asterisks (**).

            input_column (str): Column containing the source text.
            output_column (str): Column where highlighted text will be stored.
            query (str, optional): Custom query for relevance marking. If None, the pipelines global query is used. Defaults to None.
            model (str, optional): LLM model name (must be supported by LiteLLMLLMInterface). Defaults to 'gemma2'.
        """

        if model not in LiteLLMLLMInterface.supported_models:
            self.llm = None
            self.model = model
            return
        
        self.system_prompt = self.getSystemPromptWithExample()
        
        self.llm = LiteLLMLLMInterface(model=model, system_prompt=self.system_prompt)
        self.problem_llm = LiteLLMLLMInterface(model=model, system_prompt="You are a problem solving assistent. All you need to know, you will get in the prompts. Follow them exactly.")

        self.source_column_name = input_column
        self.output_column_name = output_column
        self.model = model

        if query is not None:
            self.query = query
            self.use_new_query = True
        else:
            self.query = None
            self.use_new_query = False

        self.max_number_tries = 3
        self.similarity_threshold = 0.9

        
    def transform(self, data: PipelineIntermediate, handler: PipelineStepHandler = PipelineStepHandler()):
        """
            The 'transform()' method is the core function of each pipeline step. It applies the specific modifications to the 'PipelineIntermediate' object for that step.  Apply the relevance marking step to the pipeline data.
            
            data: PipelineIntermediate -> Object which holds the current data, its metadata and the history of intermediate results.\n
            handler: PipelineStepHandler -> Object is responsible for everything related to caching, updating the progress bar/status and logging additional information.
            
            It returns the modified PipelineIntermediate object.             
        """
        
        if self.llm is None:
            raise err.PipelineStepError(err.ErrorMessages.InvalidModelName, model=self.model)
        
        if self.source_column_name not in data.documents:
            raise err.PipelineStepError(err.ErrorMessages.InvalidColumnName, column=self.source_column_name)

        full_texts = [entry if entry is not None else "" for entry in data.documents[self.source_column_name].to_list()]

        highlighted_text_list = []

        handler.update_progress(0, len(full_texts))

        for text in full_texts:
            valid_output = False
            try_counter = 0
            highlighted_text = ""
            
            while not valid_output:
                prompt = self.createPrompt(self.query if self.use_new_query else data.query, text, highlighted_text)
                potential_answer = self.llm.generate(prompt=prompt)

                valid_output, highlighted_text = self.checkAnswerValidity(potential_answer,text)

                try_counter += 1
                if try_counter > self.max_number_tries:
                    highlighted_text = text
                    valid_output = True
                           
            highlighted_text_list.append(highlighted_text)

            handler.increment_progress()

        data.documents[self.output_column_name] = highlighted_text_list
        data.set_text_column(self.output_column_name)
        data.history[str(len(data.history) + 1)] = data.documents.copy(deep=True)
        return data

    @staticmethod
    def get_info() -> dict:
        return {
            "name": RelevanceMarkingStep.get_name(),
            "category": "Metadata Analysis",
            "description": "Marking the most relevant part of the selected column in regards to the overall query or in rgeards to the query given for this specific step.",
            "parameters": {
                'model': {
                    'title': 'LLM model',
                    'description': 'LLM model used to detect the most relevant text parts regarding the given query in the overall text.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['gemma2', 'qwen2.5', 'llama3.1'],
                    'default': 'gemma2',
                },
                'input_column': {
                    'title': 'Input column name',
                    'description': 'Column name of the column, where the full text is stored, in which the most relevant text parts should be highlighted.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['full-text'],
                    'default': 'full-text',
                },
                'output_column': {
                    'title': 'Output column name',
                    'description': 'Column name of the column, where the highlighted text is stored.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['highlight-full-text'],
                    'default': 'highlight-full-text',
                },
                'query': {
                    'title': 'Optional query',
                    'description': 'An additional query, different from the main query, used for the highlighting task. Optional.',
                    'type': 'string',
                    'required': False,
                    'default': '',
                },
            }
        }


    @staticmethod
    def get_name() -> str:
        return "Marking Relevance"
    

    def getSystemPromptWithExample(self) -> str:
        """
            Returns the system prompt with rules and an example for the LLM.
        """

        return f"""You are an assistant designed to identify and highlight the most relevant text passages in a given input text based on a specific query. Your task is to highlight the most important passages by surrounding them with two asterisks (**).
        You have to follow a given ruleset:\n
        {self.getRules()}\n
        Input format:\n
        [QUERY] your-query-here\n
        [TEXT_START] your-text-here [TEXT_END]\n\n
        Example:\n
        [QUERY] What is Lego?\n
        [TEXT_START] Lego is a popular construction toy made up of interlocking plastic bricks that allow for endless creativity. It was invented in Denmark in 1932 and has since become a global phenomenon. From simple house builds to intricate models of famous landmarks, Lego sets appeal to both children and adults. Beyond play, Lego also inspires learning in areas like engineering, design, and storytelling. [TEXT_END] \n\n
        Expected output:\n
        [ANSWER] **Lego is a popular construction toy made up of interlocking plastic bricks** that allow for endless creativity. It was invented in Denmark in 1932 and has since become a global phenomenon. From simple house builds to intricate models of famous landmarks, Lego sets appeal to both children and adults. Beyond play, **Lego also inspires learning in areas like engineering, design, and storytelling.**"""

    
    def createPrompt(self, query, input, answer) -> str:
        """
            Create the prompt for the LLM, optionally adding a new rule if the previous answer violated the ruleset.

            query (str): Query guiding the relevance marking.
            input (str): The source text to highlight.
            answer (str): The last LLM output (used if invalid).

            Returns the constructed prompt string.
        """

        prompt = f"""[QUERY] {query}\n[TEXT_START] {input}  [TEXT_END]\n\n"""
        if not answer == "":
            addional_prompt = f"""The following answer does not comply with the ruleset. First, I will provide you with the rules, which are enclosed between [RULES_START] and [RULES_END].  
            Then, you will see a query, an input text, and the corresponding answer that violated the rules.  \n
            Your task: In **one sentence**, write a **new rule or clarification** that could be added to the ruleset to help prevent this type of error in future prompts of the same kind. \n
            [RULES_START] {self.getRules()} [RULES_END]\n
            [QUERY]: {query} \n
            [TEXT_START]: {input} [TEXT_END]\n
            [ANSWER]: {answer}\n """ 

            rule = self.problem_llm.generate(addional_prompt)
            prompt = f"Additional rule for the ruleset: -) {rule}\n\n" + prompt

        return prompt
    
    def getRules(self) -> str:
        """
            Return the ruleset that the LLM must follow when highlighting text.
        """

        return """"
        -) You must not delete or modify any part of the original input text.\n
        -) You may highlight one or multiple passages as needed.\n
        -) The original input text will always be between '[TEXT_START]' and '[TEXT_END]'. Your response must include everything between these markers, including titles, headers, or URLS.\n
        -) Your response must begin with '[ANSWER]' followed by the modified text with highlights.\n"""


    def checkAnswerValidity(self, potential_answer, input_text) -> str:
        """
            Validate the LLMs output to ensure compliance with the expected format and similarity to the original text.

            potential_answer (str): The raw LLM output.
            input_text (str): The original input text for comparison.

            Returns: tuple[bool, str]: 
                - True and the cleaned highlighted text if valid.
                - False and the original answer if invalid.
        """

        match = re.match(r"\[ANSWER\]((.*\n*)+)",potential_answer)
        if match is None:
            return False, potential_answer

        altered_input = "[ANSWER] " + input_text

        similarity = SequenceMatcher(None, potential_answer, altered_input).quick_ratio()
        answer = re.sub(r"^\[ANSWER\]\s*", "", potential_answer)

        if similarity < self.similarity_threshold:
            return False, potential_answer

        return True, answer

