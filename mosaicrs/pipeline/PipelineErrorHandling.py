from enum import Enum
import string

def extractPlaceholders(error_template: str):
        formatter = string.Formatter()
        return [placeholder_name for _,placeholder_name,_,_ in formatter.parse(error_template) if placeholder_name]

#--------------------------------_Exceptions--------------------------------------------

class ErrorMessages(Enum):
    InvalidColumnName = ("INVALID COLUMN NAME", "The column '{column}' is not present in the current state of the PipelineIntermediate at the step '{step_name}'!")


class PipelineStepError(Exception):
    def __init__(self, message, **kwargs):
        self.error_type = message if isinstance(message, Enum) else None
        self.params = kwargs

        self.error_msg = f"[ERROR] - "

        if isinstance(message, ErrorMessages):
            self.error_msg += f"[{message.value[0]}]: "
            try:
                self.error_msg += message.value[1].format(**kwargs)
            except KeyError as e:
                required_keys = extractPlaceholders(message.value[1])
                provided_keys = kwargs.keys()
                missing_key_params = set(required_keys) - set(provided_keys)
                self.error_msg += "[INCOMPLETE EXCEPTION OUTPUT] " + message.value[1] + f" Missing keys for exception output: {", ".join(missing_key_params)}"
        elif isinstance(message, str):
            self.error_msg += message
        else:
            self.error_msg += "A unresolvable exception was thrown! PipelineStepError requires a string or a Enum of type 'ErrorMessage' with a tuple of two string values!"

        super().__init__(self.error_msg)

    def __str__(self):
        return self.error_msg


#--------------------------------Warnings---------------------------------------------

class WarningMessages(Enum):
    UnsupportedLanguage = ("UNSUPPORTED LANGUAGES", "The following languages are currently not supported by the pipeline step '{step_name}': {languages}.")
    Test = ("TEST", "TESTSTRING")


class PipelineStepWarning():
    def __init__(self, message, **kwargs):
        self.warning_type = message if isinstance(message, Enum) else None
        self.params = kwargs

        self.warning_msg = f"[WARNING] - "

        if isinstance(message, WarningMessages):
            self.warning_msg += f"[{message.value[0]}]: "
            try:
                self.warning_msg += message.value[1].format(**kwargs)
            except KeyError as e:
                required_keys = extractPlaceholders(message.value[1])
                provided_keys = kwargs.keys()
                missing_key_params = set(required_keys) - set(provided_keys)
                self.warning_msg += "[INCOMPLETE WARNING OUTPUT] " + message.value[1] + f" Missing keys for warning output: {", ".join(missing_key_params)}"
        elif isinstance(message, str):
            self.warning_msg += message
        else:
            self.warning_msg += "A unresolvable warning was thrown! PipelineStepWarning requires a string or a Enum of type 'WarningMessages' with a tuple of two string values!"


    def __str__(self):
        return self.warning_msg
    



