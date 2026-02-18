"""Convert Python function signatures with Google-style docstrings to Anthropic tool JSON schemas."""

import inspect
import re
import types
import typing
from typing import Any, Literal, Union, get_args, get_origin


def _python_type_to_json_schema(annotation: Any) -> dict:
    """Convert a Python type annotation to a JSON schema type dict."""
    if annotation is inspect.Parameter.empty or annotation is Any:
        return {"type": "string"}

    origin = get_origin(annotation)
    args = get_args(annotation)

    # Literal["a", "b"] -> enum
    if origin is Literal:
        values = list(args)
        if values and isinstance(values[0], str):
            return {"type": "string", "enum": values}
        elif values and isinstance(values[0], int):
            return {"type": "integer", "enum": values}
        elif values and isinstance(values[0], float):
            return {"type": "number", "enum": values}
        return {"enum": values}

    # Union[X, None] (Optional) or X | Y
    is_union = origin is Union
    if not is_union:
        try:
            is_union = isinstance(annotation, types.UnionType)
        except AttributeError:
            pass
    if is_union:
        non_none = [a for a in args if a is not type(None)]
        if non_none:
            return _python_type_to_json_schema(non_none[0])
        return {"type": "string"}

    # list / List[X]
    if origin is list or annotation is list:
        schema: dict = {"type": "array"}
        if args:
            schema["items"] = _python_type_to_json_schema(args[0])
        return schema

    # dict / Dict
    if origin is dict or annotation is dict:
        return {"type": "object"}

    # Basic scalar types
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
    }
    json_type = type_map.get(annotation)
    if json_type:
        return {"type": json_type}

    return {"type": "string"}


def _parse_google_docstring(docstring: str) -> tuple:
    """Parse a Google-style docstring into a description and per-argument descriptions.

    Args:
        docstring: The raw docstring text.

    Returns:
        A tuple of (description, {param_name: param_description}).
    """
    if not docstring:
        return "", {}

    lines = inspect.cleandoc(docstring).split("\n")

    section_headers = {
        "Args:",
        "Arguments:",
        "Returns:",
        "Return:",
        "Raises:",
        "Yields:",
        "Yield:",
        "Note:",
        "Notes:",
        "Example:",
        "Examples:",
        "Attributes:",
        "References:",
        "Todo:",
        "Todos:",
    }

    description_lines: list = []
    arg_descriptions: dict = {}
    current_section = None
    current_arg = None
    current_arg_desc: list = []

    for line in lines:
        stripped = line.strip()

        if stripped in section_headers:
            if current_arg is not None:
                arg_descriptions[current_arg] = " ".join(current_arg_desc).strip()
                current_arg = None
                current_arg_desc = []
            current_section = stripped
            continue

        if current_section is None:
            description_lines.append(stripped)
        elif current_section in ("Args:", "Arguments:"):
            match = re.match(r"(\w+)\s*(?:\(.+?\))?\s*:\s*(.*)", stripped)
            if match:
                if current_arg is not None:
                    arg_descriptions[current_arg] = " ".join(current_arg_desc).strip()
                current_arg = match.group(1)
                desc_start = match.group(2)
                current_arg_desc = [desc_start] if desc_start else []
            elif current_arg and stripped:
                current_arg_desc.append(stripped)

    if current_arg is not None:
        arg_descriptions[current_arg] = " ".join(current_arg_desc).strip()

    description = " ".join(line for line in description_lines if line).strip()
    return description, arg_descriptions


def generate_tool_schema(functions: list) -> list:
    """Generate Anthropic tool JSON schemas from a list of Python functions.

    Reads function names, type annotations, and Google-style docstrings to
    produce tool definitions compatible with the Anthropic API.

    Args:
        functions: Python callables with type annotations and Google-style
            docstrings.

    Returns:
        A list of tool schema dicts ready to pass as the ``tools`` parameter
        to the Anthropic API.
    """
    tools: list = []

    for func in functions:
        sig = inspect.signature(func)
        docstring = inspect.getdoc(func) or ""
        description, arg_descriptions = _parse_google_docstring(docstring)

        # Resolve stringified annotations (from __future__ annotations)
        try:
            hints = typing.get_type_hints(func)
        except Exception:
            hints = {}

        properties: dict = {}
        required: list = []

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue

            annotation = hints.get(param_name, param.annotation)
            prop = _python_type_to_json_schema(annotation)

            if param_name in arg_descriptions:
                prop["description"] = arg_descriptions[param_name]

            properties[param_name] = prop

            if param.default is inspect.Parameter.empty:
                required.append(param_name)

        tool: dict = {
            "name": func.__name__,
            "description": description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }
        tools.append(tool)

    return tools
