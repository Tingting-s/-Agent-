# multi-tool-agent-office-assistant

A minimal FastAPI project skeleton for a multi-tool office assistant. This version focuses on the project layout, configuration loading, health check API, and placeholder modules for agents, tools, services, and prompts.

## Tech Stack

- FastAPI
- Pydantic
- python-dotenv
- tenacity
- OpenAI Python SDK for DashScope-compatible Qwen access

## Project Structure

```text
.
|- app
|  |- agents
|  |- api
|  |- prompts
|  |- schemas
|  |- services
|  |- tools
|  `- utils
|- .env.example
|- README.md
|- requirements.txt
`- run.py
```

## Getting Started

1. Create and activate a virtual environment.

```bash
python -m venv .venv
```

PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
source .venv/bin/activate
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Create a local environment file.

```bash
copy .env.example .env
```

macOS / Linux:

```bash
cp .env.example .env
```

Required environment variables for LLM-backed tasks:

- `DASHSCOPE_API_KEY`: DashScope API key for Qwen
- `DASHSCOPE_BASE_URL`: defaults to `https://dashscope.aliyuncs.com/compatible-mode/v1`
- `QWEN_MODEL`: defaults to `qwen3.5-plus`
- `LLM_TIMEOUT`: request timeout in seconds, defaults to `30`

4. Start the application.

```bash
python run.py
```

This project is intended to be started with `python run.py`.

## Environment Variables

```env
APP_NAME=multi-tool-agent-office-assistant
APP_ENV=development
DEBUG=true
HOST=127.0.0.1
PORT=8000
API_PREFIX=
LOG_LEVEL=INFO
DASHSCOPE_API_KEY=
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen3.5-plus
LLM_TIMEOUT=30
```

Notes:

- `weather_query` still returns mock weather data and does not use the LLM.
- `email_draft`, `meeting_extraction`, and `document_summary` use the DashScope-compatible Qwen endpoint.

## API

- `GET /health`: basic health check endpoint
- `POST /tasks/execute`: route a task and execute the mapped tool workflow

### GET /health

```json
{
  "status": "ok",
  "service": "multi-tool-agent-office-assistant",
  "environment": "development"
}
```

### POST /tasks/execute

Weather request example:

```json
{
  "user_input": "Shanghai weather today",
  "context": {
    "city": "Shanghai"
  }
}
```

Weather response example:

```json
{
  "task_type": "weather_query",
  "status": "success",
  "message": "Mock weather data generated for Shanghai.",
  "structured_result": {
    "city": "Shanghai",
    "condition": "Cloudy",
    "temperature_c": 22,
    "humidity": 58,
    "wind_speed_kph": 18,
    "source": "mock",
    "route_reason": "Matched keyword 'weather' and routed to weather_query."
  },
  "retry_count": 0
}
```

Compound workflow request example:

```json
{
  "user_input": "Extract action items from meeting notes and draft an email",
  "context": {
    "meeting_text": "Weekly Product Sync\nParticipants: Alice, Bob\nAction: Prepare demo script @Alice due: 2026-04-10",
    "subject": "Weekly Sync Action Items"
  }
}
```

Email draft request example:

```json
{
  "user_input": "Draft an email to share the weekly update",
  "context": {
    "subject": "Weekly Project Update",
    "purpose": "share the latest backend progress",
    "context": "The FastAPI service is running and the Qwen integration is in progress.",
    "tone": "formal"
  }
}
```

Email draft response example:

```json
{
  "task_type": "email_draft",
  "status": "success",
  "message": "Generated email draft for 'Weekly Project Update'.",
  "structured_result": {
    "subject": "Weekly Project Update",
    "body": "Dear team,\n\nHere is the latest backend progress update ...",
    "tone": "formal",
    "route_reason": "Matched keyword 'email' and routed to email_draft."
  },
  "retry_count": 0
}
```

Meeting extraction request example:

```json
{
  "user_input": "Please extract tasks from these meeting notes",
  "context": {
    "meeting_text": "Weekly Product Sync\nParticipants: Alice, Bob, Carol\nAction: Prepare demo script @Alice due: 2026-04-10"
  }
}
```

Meeting extraction response example:

```json
{
  "task_type": "meeting_extraction",
  "status": "success",
  "message": "Extracted 1 task items from meeting notes.",
  "structured_result": {
    "summary": "Weekly sync focused on release readiness.",
    "participants": ["Alice", "Bob", "Carol"],
    "decisions": ["Keep the first release focused on mock tools."],
    "tasks": [
      {
        "task_name": "Prepare demo script",
        "owner": "Alice",
        "deadline": "2026-04-10",
        "priority": "high"
      }
    ],
    "route_reason": "Matched keyword 'meeting' and routed to meeting_extraction."
  },
  "retry_count": 0
}
```

Document summary request example:

```json
{
  "user_input": "Please summarize this document",
  "context": {
    "file_path": "tests/data/project_notes.txt"
  }
}
```

Document summary response example:

```json
{
  "task_type": "document_summary",
  "status": "success",
  "message": "Loaded and summarized document from project_notes.txt.",
  "structured_result": {
    "file_path": "tests/data/project_notes.txt",
    "file_name": "project_notes.txt",
    "file_type": "txt",
    "content": "Project Notes ...",
    "summary": "The document outlines the current project status and next steps.",
    "key_points": [
      "The project is in the scaffolding phase.",
      "The next milestone is real orchestration."
    ],
    "risks": [
      "Tool-layer coverage is still incomplete."
    ],
    "route_reason": "Matched keyword 'document' and routed to document_summary."
  },
  "retry_count": 0
}
```

Need-more-info response example:

```json
{
  "task_type": "document_summary",
  "status": "need_more_info",
  "message": "More information is required to complete document_summary. Missing: file_path.",
  "structured_result": {
    "missing_fields": [
      "file_path"
    ],
    "route_reason": "Matched keyword 'document' and routed to document_summary."
  },
  "retry_count": 0
}
```

Validation error response example:

```json
{
  "status": "error",
  "message": "Request validation failed.",
  "error_code": "request_validation_error",
  "details": {
    "errors": [
      {
        "type": "missing",
        "loc": [
          "body",
          "user_input"
        ],
        "msg": "Field required"
      }
    ]
  }
}
```

## Testing

Run the unit tests with:

```bash
pytest
```

Sample files used by the document and meeting tool tests are stored under `tests/data/`.

The current tests use fake or mocked LLM behavior for text tasks, so they do not require real network access.
