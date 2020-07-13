import time


class Timer:
    def __init__(self):
        self.starttime = time.time()

    def stop(self):
        self.stoptime = time.time()
        self.delta = round(self.stoptime - self.starttime, 2)
        return self.delta
