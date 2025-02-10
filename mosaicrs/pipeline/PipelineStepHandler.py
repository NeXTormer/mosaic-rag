from threading import Lock
import redis
import os


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


        redis_host = os.environ.get('REDIS_HOST', 'localhost')
        try:
            self.redis = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)
            if self.redis.ping():
                self.caching_enabled = True
                print("Initializing PipelineStepHandler with caching enabled")

        except redis.ConnectionError:
            self.caching_enabled = False
            print("Could not connect to redis, disabling caching...")


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
            print('Caching: {}'.format(key))

    def get_cache(self, key: str):
        if not self.caching_enabled:
            return None

        if self.redis.exists(self.step_id + key):
            if self.log_cache_requests:
                print('Requesting cache: {} - HIT'.format(key))
            self.cache_hits += 1
            return self.redis.get(self.step_id + key)
        self.cache_misses += 1
        if self.log_cache_requests:
            print('Requesting cache: {} - MISS'.format(key))
        return None


    def log_stats(self):
        if self.caching_enabled:
            print('Pipeline cache statistics: {} hits | {} misses'.format(self.cache_hits, self.cache_misses))
