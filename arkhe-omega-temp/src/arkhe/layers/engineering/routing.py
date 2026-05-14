# src/arkhe/layers/engineering/routing.py
from .error_standardization import ArkheError

class RouteStateMachine:
    def __init__(self):
        self.states = {}
        self.current = None

    def add_route(self, path: str, handler):
        self.states[path] = handler

    def navigate(self, path: str):
        if path not in self.states:
            raise ArkheError("E006", f"Route not found: {path}")
        self.current = path
        return self.states[path]()
