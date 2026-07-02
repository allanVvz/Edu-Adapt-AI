"""
Educational quality gate for adaptations.

The gate is deterministic and runs after content generation. It catches gaps
that are not syntax errors: arithmetic blocks unrelated to the learning goal,
ambiguous pictograms, and fraction concepts represented as operations.
"""
from __future__ import annotations

import re
from copy import deepcopy
from typing import Any


def apply_educational_quality_gate(
    output_data: dict | None,
    activity: dict[str, Any] | None = None,
) -> dict:
    data = deepcopy(output_data or {})
    checks: list[dict[str, str]] = []

    _remove_unrelated_fraction_calculation(data, activity or {}, checks)
    _normalize_fraction_pizza_choices(data, activity or {}, checks)
    _write_validation_summary(data, checks)
    return data


def educational_blockers(output_data: dict | None) -> list[dict[str, str]]:
    validation = (output_data or {}).get("validation", {})
    quality = validation.get("educational_quality", {})
    checks = quality.get("checks", [])
    return [
        check for check in checks
        if isinstance(check, dict) and check.get("severity") == "blocker"
    ]


def _remove_unrelated_fraction_calculation(
    data: dict,
    activity: dict[str, Any],
    checks: list[dict[str, str]],
) -> None:
    if "math_formatting" not in data:
        return
    if not _is_fraction_concept(activity, data):
        return

    data.pop("math_formatting", None)
    checks.append({
        "code": "math_formatting_fraction_false_positive",
        "severity": "fixed",
        "message": "Fração conceitual não deve ser renderizada como conta de divisão.",
    })


def _normalize_fraction_pizza_choices(
    data: dict,
    activity: dict[str, Any],
    checks: list[dict[str, str]],
) -> None:
    if not _mentions_fraction_pizza(activity, data):
        return

    interactions = data.get("interaction_options") or []
    changed = False
    for interaction in interactions:
        mapping: dict[str, str] = {}
        zones = interaction.get("zones") or []
        interaction["zones"] = [_normalize_choice(zone, mapping) for zone in zones]

        items = interaction.get("items") or []
        interaction["items"] = [_normalize_choice(item, mapping) for item in items]

        correct = interaction.get("correct_answer")
        if isinstance(correct, dict):
            if "correct_zone" in correct and correct["correct_zone"] in mapping:
                correct["correct_zone"] = mapping[correct["correct_zone"]]
                changed = True
            for key, value in list(correct.items()):
                new_key = mapping.get(key, key)
                new_value = mapping.get(value, value)
                if new_key != key:
                    correct.pop(key, None)
                    correct[new_key] = new_value
                    changed = True
                elif new_value != value:
                    correct[key] = new_value
                    changed = True
        if mapping:
            changed = True

    if changed:
        checks.append({
            "code": "fraction_pizza_pictogram_normalized",
            "severity": "fixed",
            "message": "Opções de metade/inteira foram normalizadas para pictogramas textuais distintos.",
        })


def _normalize_choice(value: Any, mapping: dict[str, str]) -> Any:
    if isinstance(value, str):
        return _normalize_choice_label(value, mapping)
    if isinstance(value, dict):
        copy = dict(value)
        name = copy.get("name")
        if isinstance(name, str):
            copy["name"] = _normalize_choice_label(name, mapping)
        return copy
    return value


def _normalize_choice_label(label: str, mapping: dict[str, str]) -> str:
    lowered = label.lower()
    cleaned = re.sub(r"\s+", " ", label).strip()
    if "metade" in lowered:
        replacement = "◐ Metade da pizza"
    elif "inteira" in lowered:
        replacement = "● Pizza inteira"
    else:
        return label

    if cleaned != replacement:
        mapping[label] = replacement
    return replacement


def _write_validation_summary(data: dict, checks: list[dict[str, str]]) -> None:
    validation = data.setdefault("validation", {})
    quality = validation.setdefault("educational_quality", {})
    previous = quality.get("checks", [])
    if not isinstance(previous, list):
        previous = []

    merged = [check for check in previous if isinstance(check, dict)]
    known = {check.get("code") for check in merged}
    for check in checks:
        if check.get("code") not in known:
            merged.append(check)
            known.add(check.get("code"))

    blockers = [check for check in merged if check.get("severity") == "blocker"]
    quality["approved"] = not blockers
    quality["checks"] = merged
    if blockers:
        validation["approved"] = False


def _mentions_fraction_pizza(activity: dict[str, Any], data: dict) -> bool:
    text = _combined_text(activity, data).lower()
    return "pizza" in text and any(term in text for term in ("metade", "inteira", "1/2", "fração", "fracao"))


def _is_fraction_concept(activity: dict[str, Any], data: dict) -> bool:
    text = _combined_text(activity, data).lower()
    has_fraction = bool(re.search(r"\b\d{1,3}/\d{1,3}\b", text))
    has_concept = any(term in text for term in ("fração", "fracao", "metade", "inteira", "partes iguais"))
    has_explicit_division = any(term in text for term in ("dividido por", "÷")) or bool(re.search(r"\d+\s/\s\d+", text))
    return has_fraction and has_concept and not has_explicit_division


def _combined_text(activity: dict[str, Any], data: dict) -> str:
    activity_text = " ".join(
        str(activity.get(key, ""))
        for key in ("title", "discipline", "statement", "question", "expected_answer", "pedagogical_objective")
    )
    return f"{activity_text} {' '.join(_collect_strings(data))}"


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
