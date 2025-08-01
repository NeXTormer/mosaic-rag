from enum import Enum

#--------------------------------_Exceptions--------------------------------------------

class InvalidColumnNameException(Exception):
    def __init__(self, invalid_name:str = ""):
        super().__init__(invalid_name)
        
        self.invalid_name = invalid_name
        self.display_name = "INVALID COLUMN NAME"

    def __str__(self):
        return f"[ERROR] - [{self.display_name}]: The column {self.invalid_name} is not present in the current state of the PipelineIntermediate!"

#--------------------------------Warnings------------------------------------------

class WarningTypes(Enum):
    UnsupportedLanguage = "UNSUPPORTED LANGUAGES"


class PipelineStepWarning():
    def __init__(self, warning_type: WarningTypes, message:str = ""):
        self.message = message
        self.warning_type = warning_type

    def __str__(self):
        return f"[WARNING] - [{self.warning_type.value}]: {self.message}"


