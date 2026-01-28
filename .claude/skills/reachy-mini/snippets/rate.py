import time

class Rate:
    def __init__(self, hz: float):
        self.dt = 1.0 / hz
        self._t = time.perf_counter()

    def sleep(self) -> None:
        now = time.perf_counter()
        target = self._t + self.dt
        if target > now:
            time.sleep(target - now)
        self._t = target
