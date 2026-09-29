"""Cálculo de aderência currículo × vaga, inspirado em como ATS (Gupy, Greenhouse etc.) ranqueiam candidatos.

A nota combina dois sinais:
- cobertura de habilidades obrigatórias e desejáveis (peso maior, obrigatórias pesam o dobro);
- sobreposição com os termos mais frequentes da vaga (o "vocabulário" do anúncio).
"""

import re

from pydantic import BaseModel

from .skills import find_skills
from .text import normalize, tokenize, top_terms

REQUIRED_WEIGHT = 2.0
DESIRED_WEIGHT = 1.0
SKILL_SHARE = 0.75  # parte da nota vinda das habilidades; o resto vem do vocabulário

_DESIRED_HEADINGS = re.compile(
    r"^\s*(?:#+\s*)?(diferencia(?:l|is)|desejavel|desejaveis|nice to have|plus|sera um diferencial)\b.*$",
    re.MULTILINE,
)
_OTHER_HEADINGS = re.compile(
    r"^\s*(?:#+\s*)?(requisitos|obrigatorio|responsabilidades|atividades|beneficios|sobre)\b.*$",
    re.MULTILINE,
)


class MatchReport(BaseModel):
    score: int
    required_skills: list[str]
    desired_skills: list[str]
    matched_required: list[str]
    matched_desired: list[str]
    missing_required: list[str]
    missing_desired: list[str]
    keyword_coverage: float
    missing_keywords: list[str]
    tips: list[str]


def normalize_keep_lines(text: str) -> str:
    return "\n".join(normalize(line) for line in text.splitlines())


def split_job_sections(job_text: str) -> tuple[str, str]:
    """Separa a vaga em (parte obrigatória, parte de diferenciais).

    Tudo que vem depois de um título como "Diferenciais" ou "Desejável" e antes do
    próximo título é tratado como desejável; o resto conta como obrigatório.
    """
    norm = normalize_keep_lines(job_text)
    desired_parts: list[str] = []
    required_parts: list[str] = []
    cursor = 0
    for match in _DESIRED_HEADINGS.finditer(norm):
        if match.start() < cursor:
            continue
        required_parts.append(norm[cursor:match.start()])
        next_heading = _OTHER_HEADINGS.search(norm, match.end())
        end = next_heading.start() if next_heading else len(norm)
        desired_parts.append(norm[match.end():end])
        cursor = end
    required_parts.append(norm[cursor:])
    return "\n".join(required_parts), "\n".join(desired_parts)


def analyze(resume_text: str, job_text: str) -> MatchReport:
    required_text, desired_text = split_job_sections(job_text)
    required = find_skills(required_text)
    desired = find_skills(desired_text) - required
    resume_skills = find_skills(resume_text)

    matched_req = required & resume_skills
    matched_des = desired & resume_skills

    total_weight = REQUIRED_WEIGHT * len(required) + DESIRED_WEIGHT * len(desired)
    skill_score = (
        (REQUIRED_WEIGHT * len(matched_req) + DESIRED_WEIGHT * len(matched_des)) / total_weight
        if total_weight
        else 1.0
    )

    job_terms = top_terms(job_text, n=25)
    resume_stems = set(tokenize(resume_text))
    present_terms = [s for s, _ in job_terms if s in resume_stems]
    keyword_coverage = len(present_terms) / len(job_terms) if job_terms else 1.0
    missing_keywords = [
        surface for s, surface in job_terms
        if s not in resume_stems and not _covered_by_skill(surface, resume_skills)
    ][:10]

    score = round(100 * (SKILL_SHARE * skill_score + (1 - SKILL_SHARE) * keyword_coverage))

    return MatchReport(
        score=score,
        required_skills=sorted(required),
        desired_skills=sorted(desired),
        matched_required=sorted(matched_req),
        matched_desired=sorted(matched_des),
        missing_required=sorted(required - resume_skills),
        missing_desired=sorted(desired - resume_skills),
        keyword_coverage=round(keyword_coverage, 2),
        missing_keywords=missing_keywords,
        tips=_tips(required - resume_skills, keyword_coverage),
    )


def _covered_by_skill(term: str, resume_skills: set[str]) -> bool:
    """O termo nomeia uma habilidade que o currículo já cobre por sinônimo (ex.: "llms" × "IA generativa")."""
    skills = find_skills(term)
    return bool(skills) and skills <= resume_skills


def _tips(missing_required: set[str], keyword_coverage: float) -> list[str]:
    tips = []
    if missing_required:
        tips.append(
            "Se você TEM experiência com "
            + ", ".join(sorted(missing_required))
            + ", deixe isso explícito com o mesmo termo usado na vaga. Se não tem, não invente: "
            "destaque experiências próximas e reais."
        )
    if keyword_coverage < 0.5:
        tips.append(
            "Menos da metade do vocabulário da vaga aparece no currículo. Reescreva as descrições "
            "de experiência usando os termos do anúncio (sem mudar os fatos)."
        )
    tips.append(
        "Use layout de coluna única e títulos padrão (Experiência, Formação, Habilidades) "
        "para o parser do ATS."
    )
    return tips
