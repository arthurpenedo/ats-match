"""Sugestões de reescrita sem IA paga: alinha o vocabulário do currículo ao da vaga, sem inventar nada.

Roda em qualquer lugar (inclusive no navegador, na demo): só regras sobre a taxonomia de habilidades.

- Habilidade que a vaga pede e o currículo TEM, mas com outra palavra (ex.: currículo diz "atendimento",
  vaga diz "Atendimento ao cliente"): sugere reescrever a linha com o termo da vaga, que é o que o ATS procura.
- Habilidade que a vaga pede e o currículo NÃO tem: não sugere reescrita. Avisa que só deve entrar se for verdade.
"""

from __future__ import annotations

from dataclasses import dataclass

from .matcher import MatchReport
from .skills import _PATTERNS
from .text import normalize


@dataclass
class LocalSuggestion:
    original: str
    rewritten: str
    reason: str


def _linha_com(resume_text: str, skill: str) -> str | None:
    """Primeira linha do currículo (com conteúdo de verdade) que menciona a habilidade por algum sinônimo."""
    for linha in resume_text.splitlines():
        limpa = linha.strip().lstrip("-*•# ").strip()
        if len(limpa.split()) < 3:
            continue
        if any(p.search(normalize(limpa)) for p in _PATTERNS[skill]):
            return limpa
    return None


def suggest_local(resume_text: str, job_text: str, report: MatchReport, limite: int = 6) -> list[LocalSuggestion]:
    sugestoes: list[LocalSuggestion] = []
    cv_norm = normalize(resume_text)
    por_linha: dict[str, list[str]] = {}  # mesma linha cobre várias habilidades: uma sugestão só
    for skill in report.matched_required + report.matched_desired:
        if normalize(skill) in cv_norm:
            continue  # o currículo já usa o mesmo termo da vaga
        if linha := _linha_com(resume_text, skill):
            por_linha.setdefault(linha, []).append(skill)
    for linha, skills in list(por_linha.items())[:limite]:
        termos = ", ".join(skills)
        aspas = ", ".join(f'"{s}"' for s in skills)
        sugestoes.append(LocalSuggestion(
            original=linha,
            rewritten=f"{linha.rstrip('.')} ({termos}).",
            reason=f"Você já tem isso, mas com outras palavras. A vaga usa {aspas}: repetir o termo exato "
                   f"ajuda o ATS a encontrar.",
        ))
    for skill in report.missing_required:
        sugestoes.append(LocalSuggestion(
            original="(não aparece no currículo)",
            rewritten=f"Só inclua \"{skill}\" se você realmente tiver essa experiência.",
            reason="A vaga exige, mas não há nada equivalente no currículo. Inventar não é uma opção: "
                   "se tiver algo parecido e real, descreva com as suas palavras.",
        ))
    return sugestoes
