from pathlib import Path

from ats_match.matcher import analyze
from ats_match.rewrite import suggest_local
from ats_match.skills import find_skills

EXEMPLOS = Path(__file__).resolve().parents[1] / "examples"


def _exemplo():
    cv = (EXEMPLOS / "curriculo.md").read_text(encoding="utf-8")
    vaga = (EXEMPLOS / "vaga.md").read_text(encoding="utf-8")
    return cv, vaga, analyze(cv, vaga)


def test_exemplo_gera_sugestoes_sem_api():
    cv, vaga, rel = _exemplo()
    sugestoes = suggest_local(cv, vaga, rel)
    assert sugestoes, "a demo mostra esta seção: ela precisa ter conteúdo no exemplo"
    reescritas = [s for s in sugestoes if not s.original.startswith("(")]
    assert reescritas and all(s.original in cv for s in reescritas)  # parte de uma linha real do currículo


def test_nunca_inventa_habilidade():
    cv, vaga, rel = _exemplo()
    tem = find_skills(cv)
    for s in suggest_local(cv, vaga, rel):
        if s.original.startswith("("):  # aviso de habilidade ausente: não é reescrita
            assert "Só inclua" in s.rewritten
        else:
            assert find_skills(s.rewritten) <= tem | find_skills(s.original) | set(rel.matched_required + rel.matched_desired)
            assert not (find_skills(s.rewritten) & set(rel.missing_required + rel.missing_desired))


def test_uma_sugestao_por_linha():
    cv, vaga, rel = _exemplo()
    originais = [s.original for s in suggest_local(cv, vaga, rel) if not s.original.startswith("(")]
    assert len(originais) == len(set(originais))


def test_curriculo_que_ja_usa_os_termos_da_vaga():
    vaga = "Requisitos obrigatórios:\n- Python\n- SQL\n"
    cv = "Experiência\n- Desenvolvi scripts em Python e consultas SQL para relatórios mensais.\n"
    assert suggest_local(cv, vaga, analyze(cv, vaga)) == []
