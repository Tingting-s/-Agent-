from __future__ import annotations

import re
from typing import Any

from app.schemas.request import TaskRequest
from app.schemas.tool_result import ToolResult


CITY_ALIAS_TO_CANONICAL: dict[str, str] = {
    "beijing": "beijing",
    "北京": "beijing",
    "北京市": "beijing",
    "shanghai": "shanghai",
    "上海": "shanghai",
    "上海市": "shanghai",
    "guangzhou": "guangzhou",
    "广州": "guangzhou",
    "广州市": "guangzhou",
    "shenzhen": "shenzhen",
    "深圳": "shenzhen",
    "深圳市": "shenzhen",
    "hangzhou": "hangzhou",
    "杭州": "hangzhou",
    "杭州市": "hangzhou",
}

CANONICAL_CITY_DISPLAY: dict[str, dict[str, str]] = {
    "beijing": {"zh": "北京", "en": "Beijing"},
    "shanghai": {"zh": "上海", "en": "Shanghai"},
    "guangzhou": {"zh": "广州", "en": "Guangzhou"},
    "shenzhen": {"zh": "深圳", "en": "Shenzhen"},
    "hangzhou": {"zh": "杭州", "en": "Hangzhou"},
}

MOCK_WEATHER_DATA: dict[str, dict[str, Any]] = {
    "beijing": {
        "condition": "Sunny",
        "temperature_c": 24,
        "humidity": 35,
        "wind_speed_kph": 12,
    },
    "shanghai": {
        "city": "Shanghai",
        "condition": "Cloudy",
        "temperature_c": 22,
        "humidity": 58,
        "wind_speed_kph": 18,
    },
    "guangzhou": {
        "condition": "Humid",
        "temperature_c": 29,
        "humidity": 78,
        "wind_speed_kph": 11,
    },
    "shenzhen": {
        "condition": "Light Rain",
        "temperature_c": 27,
        "humidity": 74,
        "wind_speed_kph": 15,
    },
    "hangzhou": {
        "condition": "Overcast",
        "temperature_c": 21,
        "humidity": 62,
        "wind_speed_kph": 10,
    },
}

CITY_EXTRACTION_PATTERNS = (
    r"(?:帮我|请|麻烦|可以|能不能|想|我要|替我)?(?:查询|查一下|查下|查查|查看|看看|帮我查询|帮我看下|查询一下)?(?P<city>[\u4e00-\u9fff]{2,6})(?:今天|明天|后天|今晚|现在)?(?:的)?天气",
    r"(?P<city>[\u4e00-\u9fff]{2,6})(?:今天|明天|后天|今晚|现在)?(?:的)?天气(?:怎么样|如何|咋样|呢|情况)?",
    r"(?P<city>[A-Za-z][A-Za-z\\s-]{1,30})\\s+(?:weather|temperature|rain)(?:\\s+today|\\s+tomorrow)?",
    r"(?:weather|temperature|rain)(?:\\s+in)?\\s+(?P<city>[A-Za-z][A-Za-z\\s-]{1,30})",
)

NON_CITY_TOKENS = {
    "帮我",
    "查询",
    "查一下",
    "查下",
    "查查",
    "查看",
    "看看",
    "天气",
    "今天",
    "明天",
    "后天",
    "怎么样",
    "如何",
    "查询天气",
    "weather",
    "temperature",
    "rain",
    "today",
    "tomorrow",
}


def _contains_chinese(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def _normalize_city_candidate(raw_city: str) -> str:
    city = raw_city.strip().strip(",.!?;:，。！？；：")
    if _contains_chinese(city):
        if city.endswith("市") and len(city) > 2:
            city = city[:-1]
        return city
    return " ".join(city.split()).title()


def _resolve_city(raw_city: str) -> tuple[str | None, str]:
    normalized_city = _normalize_city_candidate(raw_city)
    lookup_key = normalized_city.lower() if not _contains_chinese(normalized_city) else normalized_city
    canonical_key = CITY_ALIAS_TO_CANONICAL.get(lookup_key)

    if canonical_key is None:
        return None, normalized_city

    display_language = "zh" if _contains_chinese(raw_city) else "en"
    display_city = CANONICAL_CITY_DISPLAY[canonical_key][display_language]
    return canonical_key, display_city


def _looks_like_city_candidate(candidate: str) -> bool:
    normalized_candidate = candidate.strip().lower()
    if not normalized_candidate:
        return False
    if normalized_candidate in NON_CITY_TOKENS:
        return False
    if any(token in normalized_candidate for token in ("天气", "weather", "temperature", "rain")):
        return False
    return True


def extract_city_from_user_input(user_input: str) -> str | None:
    text = user_input.strip()
    if not text:
        return None

    chinese_aliases = sorted(
        (alias for alias in CITY_ALIAS_TO_CANONICAL if _contains_chinese(alias)),
        key=len,
        reverse=True,
    )
    for alias in chinese_aliases:
        if alias in text:
            _, display_city = _resolve_city(alias)
            return display_city

    english_aliases = sorted(
        (alias for alias in CITY_ALIAS_TO_CANONICAL if not _contains_chinese(alias)),
        key=len,
        reverse=True,
    )
    lowered_text = text.lower()
    for alias in english_aliases:
        if re.search(rf"\b{re.escape(alias)}\b", lowered_text):
            _, display_city = _resolve_city(alias)
            return display_city

    for pattern in CITY_EXTRACTION_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        candidate = _normalize_city_candidate(match.group("city"))
        if not _looks_like_city_candidate(candidate):
            continue
        _, display_city = _resolve_city(candidate)
        return display_city

    return None


def get_weather(city: str) -> ToolResult:
    normalized_city = city.strip()
    if not normalized_city:
        return ToolResult(
            tool_name="weather_tool",
            status="error",
            message="City name is required.",
            output={},
            error="Missing city value.",
        )

    canonical_key, display_city = _resolve_city(normalized_city)
    weather = MOCK_WEATHER_DATA.get(
        canonical_key or normalized_city.lower(),
        {
            "condition": "Partly Cloudy",
            "temperature_c": 23,
            "humidity": 50,
            "wind_speed_kph": 14,
        },
    )

    return ToolResult(
        tool_name="weather_tool",
        status="success",
        message=f"Mock weather data generated for {display_city}.",
        output={
            "city": display_city,
            "condition": weather["condition"],
            "temperature_c": weather["temperature_c"],
            "humidity": weather["humidity"],
            "wind_speed_kph": weather["wind_speed_kph"],
            "source": "mock",
        },
    )


class WeatherTool:
    name = "weather_tool"

    def run(self, request: TaskRequest) -> ToolResult:
        city = str(request.get_input_value("city") or extract_city_from_user_input(request.user_input) or "")
        return get_weather(city)


# Override the legacy free-form extractor with a stricter known-city matcher.
_CITY_VARIANTS: dict[str, dict[str, tuple[str, ...]]] = {
    "beijing": {
        "en": ("beijing",),
        "zh": ("\u5317\u4eac", "\u5317\u4eac\u5e02"),
    },
    "shanghai": {
        "en": ("shanghai",),
        "zh": ("\u4e0a\u6d77", "\u4e0a\u6d77\u5e02"),
    },
    "guangzhou": {
        "en": ("guangzhou",),
        "zh": ("\u5e7f\u5dde", "\u5e7f\u5dde\u5e02"),
    },
    "shenzhen": {
        "en": ("shenzhen",),
        "zh": ("\u6df1\u5733", "\u6df1\u5733\u5e02"),
    },
    "hangzhou": {
        "en": ("hangzhou",),
        "zh": ("\u676d\u5dde", "\u676d\u5dde\u5e02"),
    },
}

_CITY_DISPLAY: dict[str, dict[str, str]] = {
    "beijing": {"en": "Beijing", "zh": "\u5317\u4eac"},
    "shanghai": {"en": "Shanghai", "zh": "\u4e0a\u6d77"},
    "guangzhou": {"en": "Guangzhou", "zh": "\u5e7f\u5dde"},
    "shenzhen": {"en": "Shenzhen", "zh": "\u6df1\u5733"},
    "hangzhou": {"en": "Hangzhou", "zh": "\u676d\u5dde"},
}

_STRICT_MOCK_WEATHER_DATA: dict[str, dict[str, Any]] = {
    "beijing": {
        "condition": "Sunny",
        "temperature_c": 24,
        "humidity": 35,
        "wind_speed_kph": 12,
    },
    "shanghai": {
        "condition": "Cloudy",
        "temperature_c": 22,
        "humidity": 58,
        "wind_speed_kph": 18,
    },
    "guangzhou": {
        "condition": "Humid",
        "temperature_c": 29,
        "humidity": 78,
        "wind_speed_kph": 11,
    },
    "shenzhen": {
        "condition": "Light Rain",
        "temperature_c": 27,
        "humidity": 74,
        "wind_speed_kph": 15,
    },
    "hangzhou": {
        "condition": "Overcast",
        "temperature_c": 21,
        "humidity": 62,
        "wind_speed_kph": 10,
    },
}


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def _clean_city_text(value: str) -> str:
    cleaned = value.strip().strip(",.!?;:，。！？；：")
    if _contains_cjk(cleaned) and cleaned.endswith("\u5e02") and len(cleaned) > 2:
        return cleaned[:-1]
    if _contains_cjk(cleaned):
        return cleaned
    return " ".join(cleaned.split()).title()


def _match_known_city(text: str) -> tuple[str | None, str | None]:
    normalized_text = text.strip()
    lowered_text = normalized_text.lower()

    for canonical, variants in _CITY_VARIANTS.items():
        for alias in variants["zh"]:
            if alias in normalized_text:
                return canonical, "zh"

    for canonical, variants in _CITY_VARIANTS.items():
        for alias in variants["en"]:
            if re.search(rf"\b{re.escape(alias)}\b", lowered_text):
                return canonical, "en"

    return None, None


def extract_city_from_user_input(user_input: str) -> str | None:
    text = user_input.strip()
    if not text:
        return None

    canonical, language = _match_known_city(text)
    if canonical is None or language is None:
        return None
    return _CITY_DISPLAY[canonical][language]


def get_weather(city: str) -> ToolResult:
    normalized_city = _clean_city_text(city)
    if not normalized_city:
        return ToolResult(
            tool_name="weather_tool",
            status="error",
            message="City name is required.",
            output={},
            error="Missing city value.",
        )

    canonical, language = _match_known_city(normalized_city)
    display_city = normalized_city
    if canonical and language:
        display_city = _CITY_DISPLAY[canonical][language]

    weather = _STRICT_MOCK_WEATHER_DATA.get(
        canonical or normalized_city.lower(),
        {
            "condition": "Partly Cloudy",
            "temperature_c": 23,
            "humidity": 50,
            "wind_speed_kph": 14,
        },
    )

    return ToolResult(
        tool_name="weather_tool",
        status="success",
        message=f"Mock weather data generated for {display_city}.",
        output={
            "city": display_city,
            "condition": weather["condition"],
            "temperature_c": weather["temperature_c"],
            "humidity": weather["humidity"],
            "wind_speed_kph": weather["wind_speed_kph"],
            "source": "mock",
        },
    )


# Final strict override: only known city aliases are accepted from free-form text.
STRICT_CITY_ALIASES: dict[str, dict[str, tuple[str, ...]]] = {
    "beijing": {
        "en": ("beijing",),
        "zh": ("\u5317\u4eac", "\u5317\u4eac\u5e02"),
    },
    "shanghai": {
        "en": ("shanghai",),
        "zh": ("\u4e0a\u6d77", "\u4e0a\u6d77\u5e02"),
    },
    "guangzhou": {
        "en": ("guangzhou",),
        "zh": ("\u5e7f\u5dde", "\u5e7f\u5dde\u5e02"),
    },
    "shenzhen": {
        "en": ("shenzhen",),
        "zh": ("\u6df1\u5733", "\u6df1\u5733\u5e02"),
    },
    "hangzhou": {
        "en": ("hangzhou",),
        "zh": ("\u676d\u5dde", "\u676d\u5dde\u5e02"),
    },
}

STRICT_CITY_DISPLAY: dict[str, dict[str, str]] = {
    "beijing": {"en": "Beijing", "zh": "\u5317\u4eac"},
    "shanghai": {"en": "Shanghai", "zh": "\u4e0a\u6d77"},
    "guangzhou": {"en": "Guangzhou", "zh": "\u5e7f\u5dde"},
    "shenzhen": {"en": "Shenzhen", "zh": "\u6df1\u5733"},
    "hangzhou": {"en": "Hangzhou", "zh": "\u676d\u5dde"},
}


def _strict_match_known_city(text: str) -> tuple[str | None, str | None]:
    normalized_text = text.strip()
    lowered_text = normalized_text.lower()

    for canonical, variants in STRICT_CITY_ALIASES.items():
        for alias in variants["zh"]:
            if alias in normalized_text:
                return canonical, "zh"

    for canonical, variants in STRICT_CITY_ALIASES.items():
        for alias in variants["en"]:
            if re.search(rf"\b{re.escape(alias)}\b", lowered_text):
                return canonical, "en"

    return None, None


def extract_city_from_user_input(user_input: str) -> str | None:
    text = user_input.strip()
    if not text:
        return None

    canonical, language = _strict_match_known_city(text)
    if canonical is None or language is None:
        return None
    return STRICT_CITY_DISPLAY[canonical][language]


def get_weather(city: str) -> ToolResult:
    normalized_city = _clean_city_text(city)
    if not normalized_city:
        return ToolResult(
            tool_name="weather_tool",
            status="error",
            message="City name is required.",
            output={},
            error="Missing city value.",
        )

    canonical, language = _strict_match_known_city(normalized_city)
    display_city = normalized_city
    if canonical is not None and language is not None:
        display_city = STRICT_CITY_DISPLAY[canonical][language]

    weather = MOCK_WEATHER_DATA.get(
        canonical or normalized_city.lower(),
        {
            "condition": "Partly Cloudy",
            "temperature_c": 23,
            "humidity": 50,
            "wind_speed_kph": 14,
        },
    )

    return ToolResult(
        tool_name="weather_tool",
        status="success",
        message=f"Mock weather data generated for {display_city}.",
        output={
            "city": display_city,
            "condition": weather["condition"],
            "temperature_c": weather["temperature_c"],
            "humidity": weather["humidity"],
            "wind_speed_kph": weather["wind_speed_kph"],
            "source": "mock",
        },
    )
