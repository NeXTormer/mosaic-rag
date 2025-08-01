from enum import Enum
import string

#--------------------------------_Exceptions--------------------------------------------

class ErrorMessages(Enum):
    InvalidColumnName = ("INVALID COLUMN NAME", "The column '{column}' is not present in the current state of the PipelineIntermediate at the step '{step_name}'!")


class PipelineStepError(Exception):
    def __init__(self, message, **kwargs):
        self.error_type = message if isinstance(message, Enum) else None
        self.params = kwargs

        self.error_msg = f"[ERROR] - "

        if isinstance(message, Enum):
            self.error_msg += f"[{message.value[0]}]: "
            try:
                self.error_msg += message.value[1].format(**kwargs)
            except KeyError as e:
                required_keys = self.extractPlaceholders(message.value[1])
                provided_keys = kwargs.keys()
                missing_key_params = set(required_keys) - set(provided_keys)
                self.error_msg += message.value[1] + f" Missing keys for exception output: {", ".join(missing_key_params)}"
        elif isinstance(message, str):
            self.error_msg += message
        else:
            self.error_msg += "A unresolvable exception was thrown! PipelineStepError requires a string or a Enum of type 'ErrorMessage' with a tuple of two string values!"

        super().__init__(self.error_msg)

    def __str__(self):
        return self.error_msg
    
    def extractPlaceholders(self, error_template: str):
        formatter = string.Formatter()
        return [placeholder_name for _,placeholder_name,_,_ in formatter.parse(error_template) if placeholder_name]


#--------------------------------Warnings---------------------------------------------

class WarningTypes(Enum):
    UnsupportedLanguage = "UNSUPPORTED LANGUAGES"


class PipelineStepWarning():
    def __init__(self, warning_type: WarningTypes, message:str = ""):
        self.message = message
        self.warning_type = warning_type

    def __str__(self):
        return f"[WARNING] - [{self.warning_type.value}]: {self.message}"


