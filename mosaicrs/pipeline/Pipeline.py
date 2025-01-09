from typing import List, Any, Dict
from mosaicrs.pipeline.PipelineIntermediate import PipelineIntermediate
from mosaicrs.pipeline_steps import PipelineStep


class Pipeline(object):

    def __init__(self, steps: List):
        print_message("Pipeline Initialization")
        self.steps = steps

    def run(self, data: PipelineIntermediate) -> (PipelineIntermediate, bool):
        success = True
        for i, step in enumerate(self.steps):
            base_message_string = "Step: " + str(i + 1)
            try:
                print_message(base_message_string + step.get_name())
                data = step.transform(data)
            except ValueError as error:
                print_error(str(error))
                success = False
                break


        return data, success



def print_error(message: str = "", error_frame_size: int = 20):
    print(error_frame_size * "*" + message + error_frame_size * "*")


def print_message(message: str = "", printing_frame_size: int = 20):
    print(printing_frame_size * "-" + message + printing_frame_size * "-")