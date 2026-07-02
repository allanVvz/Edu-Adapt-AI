"""
Structured math formatting for activity adaptations.

This service is intentionally data-only: it detects arithmetic expressions in
Math activities and adds print/screen friendly blocks to output_data. Renderers
decide how those blocks look.
"""
from __future__ import annotations

import re
from copy import deepcopy
from typing import Any


OPERATION_SYMBOLS = {
    "addition": "+",
    "subtraction": "-",
    "multiplication": "x",
    "division": "÷",
}


OPERATION_LABELS = {
    "addition": "Soma",
    "subtraction": "Subtracao",
    "multiplication": "Multiplicacao",
    "division": "Divisao",
}


_EXPRESSION_PATTERNS = (
    ("addition", re.compile(r"(?<![\d:])(\d{1,4})\s*(?:\+|mais)\s*(\d{1,4})(?![\d:])", re.IGNORECASE)),
    ("subtraction", re.compile(r"(?<![\d:])(\d{1,4})\s*(?:-|menos)\s*(\d{1,4})(?![\d:])", re.IGNORECASE)),
    ("multiplication", re.compile(r"(?<![\d:])(\d{1,4})\s*(?:x|\*|vezes)\s*(\d{1,4})(?![\d:])", re.IGNORECASE)),
    ("division", re.compile(r"(?<![\d:])(\d{1,4})\s*(?:/|÷|dividido por)\s*(\d{1,4})(?![\d:])", re.IGNORECASE)),
)


_PROBLEM_PATTERNS = (
    ("addition", re.compile(r"\b(?:tinha|tem|havia)\s+(\d{1,4}).{0,80}\b(?:ganhou|recebeu|comprou|mais)\s+(\d{1,4})", re.IGNORECASE)),
    ("subtraction", re.compile(r"\b(?:tinha|tem|havia)\s+(\d{1,4}).{0,80}\b(?:deu|gastou|perdeu|tirou|menos)\s+(\d{1,4})", re.IGNORECASE)),
)


def enhance_math_output_data(
    output_data: dict | None,
    activity: dict[str, Any] | None = None,
) -> dict:
    """Return output_data with automatic math formatting blocks when relevant."""
    data = deepcopy(output_data or {})
    if not _is_math_activity(activity, data):
        return data

    operation = _detect_operation(activity or {}, data)
    if not operation:
        return data

    data["math_formatting"] = {
        "version": 1,
        "source": "auto_math_formatting",
        "layout": "centered_large_numbers",
        "blocks": [_build_math_block(operation)],
    }
    return data


def _is_math_activity(activity: dict[str, Any] | None, output_data: dict) -> bool:
    discipline = (activity or {}).get("discipline", "")
    if isinstance(discipline, str) and discipline.lower().startswith("matem"):
        return True
    text = " ".join(_collect_strings(output_data)).lower()
    return any(word in text for word in ("soma", "subtracao", "subtração", "multiplicacao", "multiplicação", "divisao", "divisão"))


def _detect_operation(activity: dict[str, Any], output_data: dict) -> dict[str, int | str] | None:
    haystack = " ".join(
        str(activity.get(key, ""))
        for key in ("title", "statement", "question", "expected_answer", "teacher_notes")
    )
    haystack = f"{haystack} {' '.join(_collect_strings(output_data))}"

    for operation_type, pattern in (*_EXPRESSION_PATTERNS, *_PROBLEM_PATTERNS):
        match = pattern.search(haystack)
        if match:
            left = int(match.group(1))
            right = int(match.group(2))
            if operation_type == "division" and right == 0:
                continue
            return {
                "type": operation_type,
                "left": left,
                "right": right,
            }
    return None


def _build_math_block(operation: dict[str, int | str]) -> dict[str, Any]:
    operation_type = str(operation["type"])
    left = int(operation["left"])
    right = int(operation["right"])
    symbol = OPERATION_SYMBOLS[operation_type]
    result = _calculate(operation_type, left, right)
    rows = _vertical_rows(symbol, left, right, result)
    return {
        "type": operation_type,
        "label": OPERATION_LABELS[operation_type],
        "symbol": symbol,
        "operands": [left, right],
        "result": result,
        "rows": rows,
        "steps": _steps(operation_type, left, right, result),
    }


def _calculate(operation_type: str, left: int, right: int) -> str:
    if operation_type == "addition":
        return str(left + right)
    if operation_type == "subtraction":
        return str(left - right)
    if operation_type == "multiplication":
        return str(left * right)
    quotient, remainder = divmod(left, right)
    return str(quotient) if remainder == 0 else f"{quotient} r {remainder}"


def _vertical_rows(symbol: str, left: int, right: int, result: str) -> list[dict[str, str]]:
    width = max(len(str(left)), len(str(right)) + 2, len(result)) + 1
    return [
        {"kind": "operand", "operator": "", "value": str(left).rjust(width)},
        {"kind": "operand", "operator": symbol, "value": str(right).rjust(width - 2)},
        {"kind": "line", "operator": "", "value": "-" * width},
        {"kind": "result", "operator": "", "value": result.rjust(width)},
    ]


def _steps(operation_type: str, left: int, right: int, result: str) -> list[str]:
    if operation_type == "addition":
        return [f"Some {left} com {right}.", f"Resultado: {result}."]
    if operation_type == "subtraction":
        return [f"Comece em {left}.", f"Retire {right}.", f"Resultado: {result}."]
    if operation_type == "multiplication":
        return [f"Calcule {left} vezes {right}.", f"Resultado: {result}."]
    return [f"Divida {left} por {right}.", f"Resultado: {result}."]


def _collect_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            parts.extend(_collect_strings(item))
        return parts
    if isinstance(value, dict):
        parts = []
        for item in value.values():
            parts.extend(_collect_strings(item))
        return parts
    return []
