from ats_match import analyze
from ats_match.llm import build_prompt
from ats_match.matcher import normalize_keep_lines


def test_normalize_keep_lines_preserva_quebras_de_linha():
    saida = normalize_keep_lines("Diferenciais\nPython e SQL")
    assert saida.count("\n") == 1
    assert saida.splitlines()[0].strip() == saida.splitlines()[0]


def test_normalize_keep_lines_texto_vazio():
    assert normalize_keep_lines("") == ""


def test_build_prompt_inclui_curriculo_vaga_e_analise():
    relatorio = analyze("Python, SQL e Docker", "Vaga pede Python e Kubernetes")
    prompt = build_prompt("MEU CURRICULO", "MINHA VAGA", relatorio)
    assert "<curriculo>\nMEU CURRICULO\n</curriculo>" in prompt
    assert "<vaga>\nMINHA VAGA\n</vaga>" in prompt
    assert "<analise_ats>" in prompt and relatorio.model_dump_json(indent=2) in prompt
    assert prompt.rstrip().endswith("reescritas de trechos do currículo.")
