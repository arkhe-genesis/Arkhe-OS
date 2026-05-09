#!/usr/bin/env python3
"""
agi/system32/config/loader.py — Configuration Loader with Schema Validation
Substrate: Operational Integrity (325)
"""
import json
import yaml
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional, Union, Tuple, List
from dataclasses import dataclass, field, asdict
from enum import Enum

class ConfigScope(Enum):
    GLOBAL = "global"
    SUBSTRATE = "substrate"
    NODE = "node"
    USER = "user"

@dataclass
class ConfigValue:
    """A configuration value with metadata."""
    value: Any
    scope: ConfigScope
    source: str
    hash: str
    sealed: bool = False

    def verify_integrity(self) -> bool:
        """Verify that value hasn't been tampered with."""
        computed = hashlib.sha256(
            json.dumps(self.value, sort_keys=True).encode()
        ).hexdigest()
        return computed == self.hash

@dataclass
class ConfigSchema:
    """Schema definition for configuration validation."""
    name: str
    version: str
    fields: Dict[str, Dict]
    required: list = field(default_factory=list)
    defaults: Dict[str, Any] = field(default_factory=dict)

    def validate(self, config: Dict) -> Tuple[bool, List[str]]:
        """Validate config against schema. Returns (valid, errors)."""
        errors = []
        # Check required fields
        for req in self.required:
            if req not in config:
                errors.append(f"Missing required field: {req}")
        # Check field types and constraints
        for field_name, constraints in self.fields.items():
            if field_name not in config:
                continue
            value = config[field_name]
            if "type" in constraints:
                expected = constraints["type"]
                if not isinstance(value, expected):
                    errors.append(f"Field {field_name}: expected {expected}, got {type(value)}")
            if "min" in constraints and value < constraints["min"]:
                errors.append(f"Field {field_name}: value {value} below minimum {constraints['min']}")
            if "max" in constraints and value > constraints["max"]:
                errors.append(f"Field {field_name}: value {value} above maximum {constraints['max']}")
        return len(errors) == 0, errors

class ConfigLoader:
    """Unified configuration loader with schema validation and integrity verification."""

    SCHEMAS: Dict[str, ConfigSchema] = {}

    @classmethod
    def register_schema(cls, name: str, schema: ConfigSchema):
        """Register a configuration schema."""
        cls.SCHEMAS[name] = schema

    @classmethod
    def load(cls, path: Union[str, Path],
             schema_name: Optional[str] = None,
             allow_missing: bool = True) -> Dict[str, Any]:
        """Load configuration from file with optional schema validation."""
        path = Path(path)

        if not path.exists():
            if allow_missing:
                return cls._get_defaults(schema_name)
            raise FileNotFoundError(f"Config not found: {path}")

        # Parse file
        with open(path, 'r') as f:
            if path.suffix in ('.yaml', '.yml'):
                config = yaml.safe_load(f) or {}
            elif path.suffix == '.json':
                config = json.load(f)
            else:
                raise ValueError(f"Unsupported config format: {path.suffix}")

        # Validate against schema if provided
        if schema_name and schema_name in cls.SCHEMAS:
            schema = cls.SCHEMAS[schema_name]
            valid, errors = schema.validate(config)
            if not valid:
                raise ValueError(f"Config validation failed: {'; '.join(errors)}")
            # Apply defaults for missing optional fields
            for field_name, default in schema.defaults.items():
                if field_name not in config:
                    config[field_name] = default

        # Wrap values with metadata for integrity tracking
        # Actually returning unwrapped config as the cli expects it directly for simple values
        return config

    @classmethod
    def _get_defaults(cls, schema_name: Optional[str]) -> Dict[str, Any]:
        """Get default configuration values."""
        if schema_name and schema_name in cls.SCHEMAS:
            return cls.SCHEMAS[schema_name].defaults.copy()
        return {}

    @classmethod
    def _wrap_with_metadata(cls, config: Dict, source: str) -> Dict[str, ConfigValue]:
        """Wrap config values with integrity metadata."""
        wrapped = {}
        for key, value in config.items():
            if isinstance(value, dict):
                wrapped[key] = cls._wrap_with_metadata(value, f"{source}.{key}")
            else:
                hash_val = hashlib.sha256(
                    json.dumps(value, sort_keys=True).encode()
                ).hexdigest()
                wrapped[key] = ConfigValue(
                    value=value,
                    scope=ConfigScope.GLOBAL,
                    source=source,
                    hash=hash_val
                )
        return wrapped

    @classmethod
    def merge(cls, *configs: Dict) -> Dict[str, Any]:
        """Deep merge multiple configuration dictionaries."""
        result = {}
        for config in configs:
            for key, value in config.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = cls.merge(result[key], value)
                else:
                    result[key] = value
        return result

# Register default schemas
ConfigLoader.register_schema("global", ConfigSchema(
    name="arkhe-global",
    version="1.0.0",
    fields={
        "coherence_threshold": {"type": float, "min": 0.0, "max": 1.0},
        "max_context_length": {"type": int, "min": 1, "max": 8192},
        "enable_rcp": {"type": bool},
        "federation_mode": {"type": str, "choices": ["disabled", "passive", "active"]},
    },
    required=["coherence_threshold"],
    defaults={
        "coherence_threshold": 0.75,
        "max_context_length": 2048,
        "enable_rcp": True,
        "federation_mode": "passive",
    }
))

ConfigLoader.register_schema("coherence", ConfigSchema(
    name="coherence-kernel",
    version="1.0.0",
    fields={
        "lambda_align": {"type": float, "min": 0.0, "max": 1.0},
        "lambda_safety": {"type": float, "min": 0.0, "max": 1.0},
        "retrocausal_weight": {"type": float, "min": 0.0, "max": 1.0},
    },
    defaults={
        "lambda_align": 0.3,
        "lambda_safety": 0.2,
        "retrocausal_weight": 0.15,
    }
))
