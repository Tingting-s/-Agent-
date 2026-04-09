from app.tools.weather_tool import extract_city_from_user_input, get_weather


def test_get_weather_returns_mock_data() -> None:
    result = get_weather("Shanghai")

    assert result.status == "success"
    assert result.tool_name == "weather_tool"
    assert result.output["city"] == "Shanghai"
    assert result.output["source"] == "mock"
    assert "temperature_c" in result.output


def test_get_weather_requires_city() -> None:
    result = get_weather("   ")

    assert result.status == "error"
    assert result.error == "Missing city value."


def test_extract_city_from_chinese_weather_query() -> None:
    city = extract_city_from_user_input("帮我查询北京今天天气")

    assert city == "北京"


def test_extract_city_from_chinese_weather_query_variant() -> None:
    city = extract_city_from_user_input("查一下广州天气")

    assert city == "广州"


def test_extract_city_from_user_input_returns_none_when_missing() -> None:
    city = extract_city_from_user_input("帮我查询今天天气")

    assert city is None
