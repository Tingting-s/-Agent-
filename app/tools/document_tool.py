from __future__ import annotations

from pathlib import Path

from app.schemas.request import TaskRequest
from app.schemas.task_result import DocumentSummaryResult
from app.schemas.tool_result import ToolResult
from app.utils.file_loader import load_text_file


SUPPORTED_EXTENSIONS = {".txt", ".md"}


def _build_preview(content: str, limit: int = 200) -> str:
    flattened = " ".join(line.strip() for line in content.splitlines() if line.strip())
    return flattened[:limit]


def _extract_keywords(content: str, limit: int = 5) -> list[str]:
    candidates: list[str] = []
    for word in content.replace("#", " ").replace("-", " ").split():
        token = word.strip(".,:;!?()[]{}\"'").lower()
        if len(token) >= 5 and token.isalpha() and token not in candidates:
            candidates.append(token)
        if len(candidates) >= limit:
            break
    return candidates


def read_document(file_path: str) -> ToolResult:
    path = Path(file_path)
    if not path.exists():
        return ToolResult(
            tool_name="document_tool",
            status="error",
            message="Document file was not found.",
            output={"file_path": str(path)},
            error=f"File does not exist: {path}",
        )

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return ToolResult(
            tool_name="document_tool",
            status="error",
            message="Unsupported document type.",
            output={"file_path": str(path), "supported_extensions": sorted(SUPPORTED_EXTENSIONS)},
            error="Only .txt and .md files are supported.",
        )

    try:
        content = load_text_file(path)
    except (OSError, UnicodeDecodeError) as exc:
        return ToolResult(
            tool_name="document_tool",
            status="error",
            message="Failed to read document content.",
            output={"file_path": str(path)},
            error=str(exc),
        )
    lines = content.splitlines()
    non_empty_lines = [line.strip() for line in lines if line.strip()]
    title = non_empty_lines[0].lstrip("# ").strip() if non_empty_lines else path.stem.replace("_", " ").title()
    summary = DocumentSummaryResult(
        title=title,
        summary=_build_preview(content, limit=120) or "Empty document.",
        key_points=non_empty_lines[:3],
        keywords=_extract_keywords(content),
    )

    return ToolResult(
        tool_name="document_tool",
        status="success",
        message=f"Loaded document from {path.name}.",
        output={
            "file_path": str(path),
            "file_name": path.name,
            "file_type": path.suffix.lower().lstrip("."),
            "content": content,
            "line_count": len(lines),
            "char_count": len(content),
            "summary": summary.model_dump(),
        },
    )


class DocumentTool:
    name = "document_tool"

    def run(self, request: TaskRequest) -> ToolResult:
        context = request.context or {}
        file_path = str(context.get("file_path") or request.user_input)
        return read_document(file_path)


from app.services.llm_service import LLMServiceError, get_qwen_llm_service


def read_document(file_path: str) -> ToolResult:
    path = Path(file_path)
    if not path.exists():
        return ToolResult(
            tool_name="document_tool",
            status="error",
            message="Document file was not found.",
            output={"file_path": str(path)},
            error=f"File does not exist: {path}",
        )

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return ToolResult(
            tool_name="document_tool",
            status="error",
            message="Unsupported document type.",
            output={"file_path": str(path), "supported_extensions": sorted(SUPPORTED_EXTENSIONS)},
            error="Only .txt and .md files are supported.",
        )

    try:
        content = load_text_file(path)
    except (OSError, UnicodeDecodeError) as exc:
        return ToolResult(
            tool_name="document_tool",
            status="error",
            message="Failed to read document content.",
            output={"file_path": str(path)},
            error=str(exc),
        )

    if not content.strip():
        return ToolResult(
            tool_name="document_tool",
            status="error",
            message="Document content is empty.",
            output={"file_path": str(path), "file_name": path.name},
            error="The document does not contain readable text.",
        )

    try:
        summary_result = get_qwen_llm_service().summarize_document(content)
    except LLMServiceError as exc:
        return ToolResult(
            tool_name="document_tool",
            status="error",
            message="Failed to summarize the document.",
            output={
                "file_path": str(path),
                "file_name": path.name,
                "file_type": path.suffix.lower().lstrip("."),
            },
            error=str(exc),
        )

    lines = content.splitlines()
    return ToolResult(
        tool_name="document_tool",
        status="success",
        message=f"Loaded and summarized document from {path.name}.",
        output={
            "file_path": str(path),
            "file_name": path.name,
            "file_type": path.suffix.lower().lstrip("."),
            "content": content,
            "line_count": len(lines),
            "char_count": len(content),
            **summary_result,
        },
    )


class DocumentTool:
    name = "document_tool"

    def run(self, request: TaskRequest) -> ToolResult:
        file_path = str(request.get_input_value("file_path") or request.user_input)
        return read_document(file_path)
