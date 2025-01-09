from typing import List, Any, Dict
from mosaicrs.data_source import DataSource
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline_steps import PipelineStep

class Pipeline(object):

    def __init__(self, steps: List):
        self.print_message("Pipeline Initialization")
        self.steps = steps
        
    def print_message(self, message:str = "", printing_frame_size:int=20):
        print(printing_frame_size*"-" + message + printing_frame_size*"-")

    def print_error(self, message:str = "", error_frame_size:int=20):
        print(error_frame_size*"*"+message+error_frame_size*"*")

    def run(self, data: PipelineIntermediate) -> PipelineIntermediate:
        success = True
        for i, step in enumerate(self.steps):
            base_message_string = "Step: " + str(i+1)
            try:
                if issubclass(type(step), DataSource.DataSource):
                    self.print_message(base_message_string + " - DataSource")
                    data = step.request_data(data)
                else:
                    self.print_message(base_message_string + " - PipelineStep: " + step.get_name())
                    data = step.transform(data)
            except ValueError as error:
                print_error(error)
                success = False
                break


        return data, success

