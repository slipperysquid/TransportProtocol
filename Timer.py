
import time

class Timer():
    

    def __init__(self, duration):
        self._start_time = -1
        self._duration = duration

    def start(self):
        if self._start_time == -1:
            self._start_time = time.time()

    def stop(self):
        if self._start_time != -1:
            self._start_time = -1


    def is_timing(self):
        return self._start_time != -1

    def notify_timeout(self):
        if not self.is_timing():
            return False
        else:
            return time.time() - self._start_time >= self._duration
    