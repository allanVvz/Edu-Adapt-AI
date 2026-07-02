from copy import deepcopy
from typing import Any

from .openai_service import _API_BASE_URL
from .math_formatting_service import enhance_math_output_data
from .educational_validation_service import apply_educational_quality_gate


def normalize_static_urls(value: Any, api_base_url: str | None = None) -> Any:
    """Replace stale absolute static URLs with the current API base URL."""
    base_url = (api_base_url or _API_BASE_URL).rstrip("/")
    if isinstance(value, str):
        for marker in ("/static/audio/", "/static/images/"):
            if marker in value:
                return f"{base_url}{marker}{value.split(marker, 1)[1]}"
        return value

    if isinstance(value, list):
        return [normalize_static_urls(item, base_url) for item in value]

    if isinstance(value, dict):
        return {key: normalize_static_urls(item, base_url) for key, item in value.items()}

    return value


def normalized_output_data(
    output_data: dict | None,
    api_base_url: str | None = None,
    activity: dict | None = None,
) -> dict:
    data = enhance_math_output_data(output_data or {}, activity)
    data = apply_educational_quality_gate(data, activity)
    return normalize_static_urls(data, api_base_url)
