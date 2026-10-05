"""Simultaneous immutable joint-state updates for replay."""

from .validation import position


class Replay:
    def __init__(self, paths):
        self.paths = paths
        self.tick = 0
        self.makespan = max(len(p) - 1 for p in paths.values())

    @property
    def state(self):
        return {r: position(p, self.tick) for r, p in self.paths.items()}

    def step(self):
        self.tick = min(self.tick + 1, self.makespan)
        return self.state  # All positions read at the same tick.

    def reset(self):
        self.tick = 0
