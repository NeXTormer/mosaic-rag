# Adding a New Pipeline Step: A Step-by-Step Guide

This guide documents how to add a new pipeline step to the project. We will use the `TranslateStep` as a concrete example to demonstrate the process. A pipeline step is an individual processing unit in a larger data manipulation sequence.

There are two primary ways to create a pipeline step:
1. Inheriting from `RowProcessorPipelineStep`: Best for operations applied sequentially to individual rows (e.g., modifying text row by row). This handles iteration and caching for you.
2. Inheriting from `PipelineStep`: Best for operations that require access to the entire dataset at once (e.g., sorting, computing statistics over all rows, or re-ranking).

For our `TranslateStep`, we will translate documents one by one. Thus, we will inherit from `RowProcessorPipelineStep`.

---

## 1. Create the Pipeline Step Class

Create a new Python file in the `mosaicrs/pipeline_steps/` directory. For our example, we create `TranslateStep.py`.

### Required Imports

```python
from typing import Optional

from mosaicrs.pipeline.PipelineStepHandler import PipelineStepHandler
from mosaicrs.pipeline_steps.RowProcessorPipelineStep import RowProcessorPipelineStep
from mosaicrs.llm.LiteLLMLLMInterface import LiteLLMLLMInterface
```

### The Class Definition

Define the class inheriting from `RowProcessorPipelineStep` and implement the required methods: `__init__`, `transform_row`, `get_cache_fingerprint`, `get_info`, and `get_name`.

```python
class TranslateStep(RowProcessorPipelineStep):
    def __init__(self, input_column: str, output_column: str, target_language: str = "English"):
        """
        A pipeline step that translates text documents using the "translategemma" model via LiteLLMLLMInterface.
        """
        # 1. Call the parent class constructor
        super().__init__(input_column, output_column)

        # 2. Initialize any specific variables for your step
        self.target_language = target_language
        self.model_name = "translategemma"
        self.llm = LiteLLMLLMInterface()
        self.prompt = f"Translate the following text into {self.target_language}:\n\n"

    def transform_row(self, data: str, handler: PipelineStepHandler) -> tuple[str, Optional[str]]:
        """
        Applies the transformation (translation) to a single row of data.
        Returns the transformed string and a UI indicator (e.g., 'text', 'chip', or 'rank').
        """
        if not data:
            return "", "text"

        # Use our LLM instance to generate the translated text
        translated_text = self.llm.generate(self.prompt + data, self.model_name)

        # 'text' indicates this column should be available in the frontend's text viewer dropdown
        return translated_text, "text"

    def get_cache_fingerprint(self) -> str:
        """
        Returns a string used to identify the uniqueness of the step's configuration for caching purposes.
        If parameters change, the fingerprint should change to invalidate the cache.
        """
        return self.target_language + self.model_name + self.prompt

    @staticmethod
    def get_info() -> dict:
        """
        Provides metadata about the step, heavily used by the UI to render the configuration form.
        """
        return {
            "name": TranslateStep.get_name(),
            "category": "Pre-Processing",
            "description": "Translate documents using a local Ollama instance with the translategemma model.",
            "parameters": {
                'input_column': {
                    'title': 'Input column name',
                    'description': 'The column containing text to translate.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['full-text'],
                    'default': 'full-text',
                },
                'output_column': {
                    'title': 'Output column name',
                    'description': 'The column where translated text gets saved.',
                    'type': 'dropdown',
                    'enforce-limit': False,
                    'supported-values': ['translated_text'],
                    'default': 'translated_text',
                },
                'target_language': {
                    'title': 'Target language',
                    'description': 'The language to translate the text into.',
                    'type': 'text',
                    'enforce-limit': False,
                    'supported-values': [],
                    'default': 'English',
                },
            }
        }

    @staticmethod
    def get_name() -> str:
        """
        Returns the human-readable name of the step.
        """
        return 'Document Translator'
```

---

## 2. Register the Pipeline Step in the Application

After creating the step class, you need to inform the application that it exists so it can be dynamically loaded and selected via the UI. This is done in the `app/PipelineTask.py` file.

1. **Import the new step:**
   Open `app/PipelineTask.py` and add an import statement for your new class at the top of the file alongside the others.

   ```python
   # ... other imports
   from mosaicrs.pipeline_steps.TranslateStep import TranslateStep
   ```

2. **Add to the mapping dictionary:**
   In the same file, locate the `pipeline_steps_mapping` dictionary. Add a new key-value pair where the key is a unique string identifier (used internally) and the value is the class reference itself.

   ```python
   pipeline_steps_mapping = {
       # ... other steps
       "translate_step": TranslateStep,
   }
   ```

## Conclusion

By following these steps, you have successfully added a `TranslateStep` to the project. The UI will automatically pick up the new step by calling the `get_info()` method of all registered classes, and users can now include the `Document Translator` step in their data pipelines.
