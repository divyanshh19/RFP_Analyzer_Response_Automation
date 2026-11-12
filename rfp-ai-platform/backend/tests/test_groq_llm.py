"""Unit tests for the shared GroqCloud LLM helper and settings."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from app.core.config import settings
from app.core.llm import generate_json, generate_json_list, generate_text
from app.mcp.rfp_document_server import extract_deadlines
from app.services.extraction.requirement_extractor import extract_requirements_from_text


def _mock_groq_client(content: str) -> MagicMock:
    client = MagicMock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )
    return client


def test_groq_settings_loaded():
    assert settings.GROQ_MODEL == "qwen/qwen3.8-27b"
    assert settings.GROQ_API_KEY.startswith("gsk_")


def test_generate_text_and_json_helpers():
    text_client = _mock_groq_client("  Hello Groq  ")
    assert generate_text("Say hi", client=text_client) == "Hello Groq"

    json_client = _mock_groq_client('```json\n{"ok": true}\n```')
    assert generate_json("Return JSON", client=json_client) == {"ok": True}

    list_client = _mock_groq_client('{"deadlines": [{"event": "Submission", "date": "2026-12-31"}]}')
    result = generate_json_list("Return JSON", list_key="deadlines", client=list_client)
    assert result == [{"event": "Submission", "date": "2026-12-31"}]


def test_extract_deadlines_uses_groq_json_wrapper(monkeypatch):
    mock_client = _mock_groq_client('{"deadlines": [{"event": "Q&A Cutoff", "date": "2026-11-30"}]}')
    monkeypatch.setattr("app.core.llm.get_groq_client", lambda: mock_client)

    deadlines = extract_deadlines("Q&A Cutoff is 2026-11-30")
    assert deadlines == [{"event": "Q&A Cutoff", "date": "2026-11-30"}]
    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == settings.GROQ_MODEL
    assert call_kwargs["response_format"] == {"type": "json_object"}


def test_extract_requirements_uses_groq(monkeypatch):
    payload = '{"requirements": [{"requirement_id": "REQ-001", "description": "99.9% SLA", "category": "Technical", "priority": "HIGH", "mandatory": true}]}'
    mock_client = _mock_groq_client(payload)
    monkeypatch.setattr("app.services.extraction.requirement_extractor.get_groq_client", lambda: mock_client)

    reqs = extract_requirements_from_text("System must provide 99.9% SLA.")
    assert len(reqs) == 1
    assert reqs[0].requirement_id == "REQ-001"
    assert reqs[0].priority == "HIGH"
