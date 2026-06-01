"""Tool Contract — Define input/output schemas for tools"""
from dataclasses import dataclass, field
from typing import Any, Optional
import json


@dataclass
class ParameterSchema:
    name: str
    type: str  # "string", "integer", "boolean", "array", "object"
    description: str = ""
    required: bool = False
    default: Any = None
    enum: list[Any] = field(default_factory=list)
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: str = ""

    def to_dict(self) -> dict:
        d = {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "required": self.required,
        }
        if self.default is not None:
            d["default"] = self.default
        if self.enum:
            d["enum"] = self.enum
        if self.min_value is not None:
            d["minimum"] = self.min_value
        if self.max_value is not None:
            d["maximum"] = self.max_value
        return d

    def validate(self, value: Any) -> tuple[bool, str]:
        if value is None:
            if self.required:
                return False, f"Parameter '{self.name}' is required"
            return True, "OK"

        if self.enum and value not in self.enum:
            return False, f"Value must be one of: {self.enum}"

        type_map = {
            "string": str, "integer": int, "boolean": bool,
            "array": list, "object": dict,
        }
        expected_type = type_map.get(self.type)
        if expected_type and not isinstance(value, expected_type):
            return False, f"Expected type {self.type}, got {type(value).__name__}"

        if isinstance(value, (int, float)):
            if self.min_value is not None and value < self.min_value:
                return False, f"Value must be >= {self.min_value}"
            if self.max_value is not None and value > self.max_value:
                return False, f"Value must be <= {self.max_value}"

        if isinstance(value, str):
            if self.min_length is not None and len(value) < self.min_length:
                return False, f"String length must be >= {self.min_length}"
            if self.max_length is not None and len(value) > self.max_length:
                return False, f"String length must be <= {self.max_length}"

        return True, "OK"


@dataclass
class OutputSchema:
    type: str = "object"
    description: str = ""
    fields: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "description": self.description,
            "fields": self.fields,
        }


@dataclass
class ToolContract:
    """Define input/output contract for a tool."""
    name: str
    description: str
    version: str = "1.0.0"
    input_parameters: list[ParameterSchema] = field(default_factory=list)
    output_schema: OutputSchema = field(default_factory=OutputSchema)
    examples: list[dict] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    category: str = "custom"
    risk_level: str = "low"
    timeout_sec: int = 30
    requires_sandbox: bool = False
    deprecated: bool = False

    def validate_input(self, arguments: dict) -> tuple[bool, list[str]]:
        errors = []
        for param in self.input_parameters:
            value = arguments.get(param.name)
            valid, msg = param.validate(value)
            if not valid:
                errors.append(msg)
        return len(errors) == 0, errors

    def get_required_params(self) -> list[ParameterSchema]:
        return [p for p in self.input_parameters if p.required]

    def get_optional_params(self) -> list[ParameterSchema]:
        return [p for p in self.input_parameters if not p.required]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "input_parameters": [p.to_dict() for p in self.input_parameters],
            "output_schema": self.output_schema.to_dict(),
            "examples": self.examples,
            "tags": self.tags,
            "category": self.category,
            "risk_level": self.risk_level,
            "timeout_sec": self.timeout_sec,
            "requires_sandbox": self.requires_sandbox,
            "deprecated": self.deprecated,
        }

    def to_openai_function(self) -> dict:
        properties = {}
        required = []
        for param in self.input_parameters:
            properties[param.name] = param.to_dict()
            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def to_json_schema(self) -> dict:
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": self.name,
            "description": self.description,
            "type": "object",
            "properties": {
                p.name: p.to_dict() for p in self.input_parameters
            },
            "required": [p.name for p in self.input_parameters if p.required],
        }
