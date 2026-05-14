# src/arkhe/layers/engineering/component_library.py
import json
from .error_standardization import ArkheError

class ArkheComponent:
    def __init__(self, name, props_schema: dict):
        self.name = name
        self.schema = props_schema

    def validate_props(self, props: dict) -> bool:
        # schema validation (simple)
        for key, typ in self.schema.items():
            if key not in props or not isinstance(props[key], typ):
                return False
        return True

    def render(self, props: dict) -> str:
        if not self.validate_props(props):
            raise ArkheError("E005", f"Invalid props for {self.name}")
        # return JSON representation (for UI)
        return json.dumps({'component': self.name, 'props': props})
