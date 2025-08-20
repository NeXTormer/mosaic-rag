from enum import Enum
import string

def extractPlaceholders(error_template: str):
        formatter = string.Formatter()
        return [placeholder_name for _,placeholder_name,_,_ in formatter.parse(error_template) if placeholder_name]

#--------------------------------_Exceptions--------------------------------------------

class ErrorMessages(Enum):
    InvalidColumnName = ("INVALID COLUMN NAME", "The column '{column}' is not present in the current state of the PipelineIntermediate!")
    InvalidRankingColumn = ("INVALID RANKING COLUMN", "The ranking column '{ranking_column}' does not exist in the current pipeline intermediate.\nThe following ranking columns exist: {given_columns}")
    InvalidCoordinates = ("INVALID COORDINATE FORMAT", "The following fields have invalid values: {invalid_value_names}. The fields should only contain numerical chars seperated by a single '.'.")
    InvalidModelName = ("INVALID MODEL NAME", "Model: {model} is not supported.")

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
                self.error_msg += f'[INCOMPLETE EXCEPTION OUTPUT] {message.value[1]} Missing keys for exception output: {", ".join(missing_key_params)}'
        elif isinstance(message, str):
            self.error_msg += message
        else:
            self.error_msg += "A unresolvable exception was thrown! PipelineStepError requires a string or a Enum of type 'ErrorMessage' with a tuple of two string values!"

        super().__init__(self.error_msg)

    def __str__(self):
        return self.error_msg


#--------------------------------Warnings---------------------------------------------

class WarningMessages(Enum):
    UnsupportedLanguage = ("UNSUPPORTED LANGUAGES", "The following languages are currently not supported: {languages}.")
    TooLargeKValue = ("K-VALUE TOO LARGE", "The selected number of remaining rows after reduction is larger than the current result set. The number of remaining results is therefore set to the overall number of existing results (k={k}).")
    SentimentPredictionNotPossible = ("SENITMENT PREDICTION NOT POSSIBLE" , "The sentiment prediction with the model '{model}' failed with the exception '{exception_name}'. The input string was: {input}")
    MetricDoesNotExist = ("METRIC DOES NOT EXIST", "The selected metric does not exist, therefore we use Cosine Similarity per default.")

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
                self.warning_msg += f'[INCOMPLETE WARNING OUTPUT] {message.value[1]} Missing keys for warning output: {", ".join(missing_key_params)}'
        elif isinstance(message, str):
            self.warning_msg += message
        else:
            self.warning_msg += "A unresolvable warning was thrown! PipelineStepWarning requires a string or a Enum of type 'WarningMessages' with a tuple of two string values!"


    def __str__(self):
        return self.warning_msg
    



