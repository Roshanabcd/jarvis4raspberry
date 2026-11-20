class SimulatedAgent:
    """Deterministic mock agent; it never reads or modifies project files."""
    def __init__(self, response="simulated result", fail_times=0):
        self.response, self.fail_times, self.calls = response, fail_times, 0
        self.cancelled = False

    def execute(self, task):
        self.calls += 1
        if self.cancelled:
            raise RuntimeError("cancelled")
        if self.calls <= self.fail_times:
            raise RuntimeError("simulated failure")
        return self.response

    def cancel(self):
        self.cancelled = True
