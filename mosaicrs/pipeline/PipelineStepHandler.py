from threading import Lock

class PipelineStepHandler:

    def __init__(self):
        self.should_cancel = False
        self.progress = (0, 0)
        self.progress_lock = Lock()


    def update_progress(self, current_iteration, total_iterations):
        with self.progress_lock:
            self.progress = (current_iteration, total_iterations)

    def increment_progress(self):
        with self.progress_lock:
            self.progress = (self.progress[0] + 1, self.progress[1])


    def get_progress(self):
        with self.progress_lock:
            current = self.progress[0]
            total = self.progress[1]
            if current > total:
                current = total

            if total == 0:
                total = 1

            return {
                'step_percentage': current / total,
                'step_progress': '{}/{}'.format(current, total)
            }

    def reset(self):
        self.should_cancel = False
        self.progress = (0, 0)

    # TODO: should also handle caching in some form