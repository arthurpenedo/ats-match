import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

from ats_match import analyze, api, llm

RESUME = "Automatizei relatórios com Python e SQL no time de atendimento."
JOB = "## Requisitos\n- Python\n- SQL\n- LLMs\n"


class FakeClient:
    """Imita `anthropic.Anthropic` o suficiente para testar sem chamar a API."""

    def __init__(self, payload: dict, stop_reason: str = "end_turn"):
        self.calls: list[dict] = []
        text_block = SimpleNamespace(type="text", text=json.dumps(payload))
        response = SimpleNamespace(stop_reason=stop_reason, content=[text_block])

        def create(**kwargs):
            self.calls.append(kwargs)
            return response

        self.beta = SimpleNamespace(messages=SimpleNamespace(create=create))


def _payload(*rewrites: str) -> dict:
    return {"suggestions": [{"original": RESUME, "rewritten": r, "reason": "alinha à vaga"} for r in rewrites]}


def test_validate_suggestions_drops_invented_skills():
    honest = "Desenvolvi automações em Python e SQL para o atendimento."
    invented = "Construí pipelines RAG com LLMs em Python."
    client = FakeClient(_payload(honest, invented))
    result = llm.suggest_rewrites(RESUME, JOB, analyze(RESUME, JOB), client=client)
    assert [s.rewritten for s in result] == [honest]


def test_request_uses_structured_output_and_fallback():
    client = FakeClient(_payload("Automatizei relatórios em Python."))
    llm.suggest_rewrites(RESUME, JOB, analyze(RESUME, JOB), client=client)
    call = client.calls[0]
    assert call["model"] == llm.MODEL
    assert call["fallbacks"] == "default"
    assert call["output_config"]["format"]["type"] == "json_schema"


def test_refusal_raises():
    client = FakeClient({"suggestions": []}, stop_reason="refusal")
    try:
        llm.suggest_rewrites(RESUME, JOB, analyze(RESUME, JOB), client=client)
    except llm.RefusalError:
        return
    raise AssertionError("esperava RefusalError")


def test_api_match_endpoint():
    client = TestClient(api.app)
    resp = client.post("/match", json={"resume": RESUME, "job": JOB})
    assert resp.status_code == 200
    body = resp.json()
    assert body["missing_required"] == ["LLMs"]
    assert client.get("/health").json() == {"status": "ok"}
