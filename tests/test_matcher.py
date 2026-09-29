from pathlib import Path

from ats_match import analyze
from ats_match.matcher import split_job_sections
from ats_match.skills import find_skills
from ats_match.text import normalize, tokenize

EXAMPLES = Path(__file__).parent.parent / "examples"


def test_normalize_removes_accents_and_case():
    assert normalize("Automação em Python!") == "automacao em python"


def test_tokenize_drops_stopwords():
    assert tokenize("Experiência com Python e SQL") == ["python", "sql"]


def test_find_skills_uses_synonyms_and_word_boundaries():
    assert find_skills("Consultas no Athena e dashboards no PowerBI") == {"AWS", "Power BI"}
    # "ml" não pode casar dentro de "html"
    assert "Machine Learning" not in find_skills("Sei HTML e CSS")


def test_split_job_sections_separates_desired():
    required, desired = split_job_sections("## Requisitos\n- Python\n## Diferenciais\n- AWS\n")
    assert "python" in required and "aws" not in required
    assert "aws" in desired


def test_example_report():
    report = analyze((EXAMPLES / "curriculo.md").read_text("utf-8"), (EXAMPLES / "vaga.md").read_text("utf-8"))
    assert set(report.required_skills) >= {"Python", "SQL", "LLMs", "Prompt engineering", "Git"}
    assert "RAG" in report.desired_skills and "RAG" not in report.required_skills
    assert "RAG" in report.missing_desired
    assert {"Python", "SQL", "Git"} <= set(report.matched_required)
    assert 0 < report.score < 100


def test_perfect_match_scores_high_and_empty_resume_scores_low():
    job = "## Requisitos\n- Python\n- SQL\n"
    assert analyze("Desenvolvo em Python e SQL há 3 anos.", job).score >= 80
    assert analyze("Sou confeiteira e faço bolos.", job).score <= 20


def test_missing_required_generates_honest_tip():
    report = analyze("Trabalho com Excel.", "## Requisitos\n- Python\n")
    assert report.missing_required == ["Python"]
    assert any("não invente" in tip for tip in report.tips)
