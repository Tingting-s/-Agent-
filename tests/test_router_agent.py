from app.agents.router_agent import RouterAgent
from app.schemas.request import TaskRequest


def test_router_routes_meeting_extraction_from_keywords() -> None:
    decision = RouterAgent().route(TaskRequest(user_input="请根据会议纪要提取待办任务"))

    assert decision.task_type == "meeting_extraction"
    assert decision.steps == ("meeting_extraction",)


def test_router_routes_document_summary_from_keywords() -> None:
    decision = RouterAgent().route(TaskRequest(user_input="请帮我总结这个文档"))

    assert decision.task_type == "document_summary"
    assert decision.steps == ("document_summary",)


def test_router_routes_weather_query_from_keywords() -> None:
    decision = RouterAgent().route(TaskRequest(user_input="今天上海会下雨吗，温度怎么样"))

    assert decision.task_type == "weather_query"
    assert decision.steps == ("weather_query",)


def test_router_routes_email_draft_from_keywords() -> None:
    decision = RouterAgent().route(TaskRequest(user_input="帮我写一封邮件草稿发给团队"))

    assert decision.task_type == "email_draft"
    assert decision.steps == ("email_draft",)


def test_router_routes_compound_meeting_to_email_workflow() -> None:
    decision = RouterAgent().route(TaskRequest(user_input="根据会议纪要提取任务项并生成邮件草稿"))

    assert decision.task_type == "email_draft"
    assert decision.steps == ("meeting_extraction", "email_draft")
