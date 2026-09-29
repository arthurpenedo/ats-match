"""Camada opcional de LLM: sugere reescritas de trechos do currículo alinhadas à vaga.

Regra de ouro: a IA só pode REORGANIZAR e REESCREVER fatos que já estão no currículo.
Toda sugestão passa por `validate_suggestions`, que descarta qualquer uma que introduza
uma habilidade ausente do currículo original.
"""

import json
import os

import anthropic
from pydantic import BaseModel, ConfigDict

from .matcher import MatchReport
from .skills import find_skills

MODEL = os.getenv("ATS_MATCH_MODEL", "claude-opus-5-5")

SYSTEM_PROMPT = """Você é um especialista em recrutamento e em como sistemas ATS (Gupy, Greenhouse, \
Workday) leem currículos. Sua tarefa é sugerir reescritas de trechos do currículo para que ele use \
a linguagem da vaga.

Regras inegociáveis:
- Use APENAS fatos, ferramentas e experiências que já estão no currículo. Nunca invente habilidade, \
cargo, número ou certificação.
- Se a vaga pede algo que o currículo não tem, não tente disfarçar: ignore esse ponto.
- Escreva em português do Brasil, em bullets objetivos, com verbo de ação no início.
- Cada sugestão deve citar o trecho original que está sendo reescrito."""


class Suggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    original: str
    rewritten: str
    reason: str


class SuggestionList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    suggestions: list[Suggestion]


class RefusalError(RuntimeError):
    """O modelo recusou o pedido (stop_reason == "refusal")."""


def build_prompt(resume_text: str, job_text: str, report: MatchReport) -> str:
    return (
        f"<curriculo>\n{resume_text}\n</curriculo>\n\n<vaga>\n{job_text}\n</vaga>\n\n"
        f"<analise_ats>\n{report.model_dump_json(indent=2)}\n</analise_ats>\n\n"
        "Sugira de 3 a 6 reescritas de trechos do currículo."
    )


def suggest_rewrites(
    resume_text: str,
    job_text: str,
    report: MatchReport,
    client: anthropic.Anthropic | None = None,
) -> list[Suggestion]:
    client = client or anthropic.Anthropic()
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=SYSTEM_PROMPT,
        output_config={
            "effort": "medium",
            "format": {"type": "json_schema", "schema": SuggestionList.model_json_schema()},
        },
        messages=[{"role": "user", "content": build_prompt(resume_text, job_text, report)}],
    )
    if response.stop_reason == "refusal":
        raise RefusalError("O modelo recusou gerar sugestões para este conteúdo.")
    text = next(block.text for block in response.content if block.type == "text")
    parsed = SuggestionList.model_validate(json.loads(text))
    return validate_suggestions(resume_text, parsed.suggestions)


def validate_suggestions(resume_text: str, suggestions: list[Suggestion]) -> list[Suggestion]:
    """Descarta sugestões que mencionem habilidades que não existem no currículo."""
    resume_skills = find_skills(resume_text)
    return [s for s in suggestions if find_skills(s.rewritten) <= resume_skills]
