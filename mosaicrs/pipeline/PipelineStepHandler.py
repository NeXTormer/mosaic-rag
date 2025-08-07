from threading import Lock
import redis
import os
import datetime

from mosaicrs.pipeline.PipelineErrorHandling import PipelineStepWarning


class PipelineStepHandler:

    def __init__(self):
        self.should_cancel = False
        self.progress = (0, 0)
        self.progress_lock = Lock()
        self.step_id = ''

        self.cache_hits = 0
        self.cache_misses = 0

        self.log_cache_requests = False

        self.caching_enabled = False

        self.logs = []
        self.logs_lock = Lock()

        self.warnings = []
        self.warnings_lock = Lock()

        self.error = (0, '')


        redis_host = os.environ.get('REDIS_HOST', 'localhost')
        try:
            self.redis = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)
            if self.redis.ping():
                self.caching_enabled = True
                self.log("Initializing PipelineStepHandler with caching enabled")

        except redis.ConnectionError:
            self.caching_enabled = False
            self.log("Could not connect to redis, disabling caching...")


    def update_progress(self, current_iteration, total_iterations):
        with self.progress_lock:
            self.progress = (current_iteration, total_iterations)

    def increment_progress(self):
        with self.progress_lock:
            self.progress = (self.progress[0] + 1, self.progress[1])


    def get_status(self):
        data = {}
        with self.progress_lock:
            current = self.progress[0]
            total = self.progress[1]
            if current > total:
                current = total

            if total == 0:
                total = 1

            data['step_percentage'] = current / total
            data['step_progress'] = '{}/{}'.format(current, total)


        with self.logs_lock:
            data['log'] = self.logs

        with self.warnings_lock:
            data['warnings'] = self.warnings


        return data

    def reset(self, step_id: str):
        self.should_cancel = False
        self.progress = (0, 0)
        self.step_id = step_id


    def put_cache(self, key: str, value: str):
        if not self.caching_enabled:
            return

        if value is None:
            value = ''

        if key is None:
            return

        self.redis.set(self.step_id + key, value)
        if self.log_cache_requests:
            self.log('Caching: {}'.format(key))

    def get_cache(self, key: str):
        if not self.caching_enabled:
            return None

        if self.redis.exists(self.step_id + key):
            if self.log_cache_requests:
                self.log('Requesting cache: {} - HIT'.format(key))
            self.cache_hits += 1
            return self.redis.get(self.step_id + key)
        self.cache_misses += 1
        if self.log_cache_requests:
            self.log('Requesting cache: {} - MISS'.format(key))
        return None


    def log(self, message: str):
        with self.logs_lock:
            msg = '{}: {}'.format(datetime.datetime.now().time(), message)
            self.logs.append(msg)
            print(msg)

    def warning(self, warning: PipelineStepWarning):
        with self.warnings_lock:
            self.warnings.append(warning.warning_msg)
            print(f'[WARNING] in {self.step_id}' + warning.warning_msg)


    def get_cache_hit_ratio(self):
        if self.caching_enabled:
            if (self.cache_misses + self.cache_hits) == 0:
                return 0
            return float(self.cache_hits) / float(self.cache_misses + self.cache_hits)
        return 0

    def log_cache_statistics(self):
        if self.caching_enabled:
            self.log('Cache statistics: {} hits | {} misses'.format(self.cache_hits, self.cache_misses))
