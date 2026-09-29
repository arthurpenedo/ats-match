"""Interface web do ats-match: `streamlit run streamlit_app.py`."""

import os
from pathlib import Path

import streamlit as st

from ats_match import analyze
from ats_match.extract import ExtractionError, extract_text

EXAMPLES = Path(__file__).parent / "examples"

st.set_page_config(page_title="ats-match", page_icon="🎯", layout="wide")

st.title("🎯 ats-match")
st.caption(
    "Veja seu currículo como um ATS (Gupy, Greenhouse, Workday) vê: nota de aderência à vaga, "
    "habilidades que faltam e o vocabulário do anúncio que não aparece no seu texto."
)

if st.button("Carregar exemplo (candidata e vaga fictícias)"):
    st.session_state["cv_text"] = (EXAMPLES / "curriculo.md").read_text(encoding="utf-8")
    st.session_state["job_text"] = (EXAMPLES / "vaga.md").read_text(encoding="utf-8")

col_cv, col_job = st.columns(2)
with col_cv:
    st.subheader("Currículo")
    upload = st.file_uploader("Envie PDF, DOCX, MD ou TXT", type=["pdf", "docx", "md", "txt"])
    if upload is not None:
        try:
            st.session_state["cv_text"] = extract_text(upload.getvalue(), upload.name)
        except ExtractionError as exc:
            st.error(str(exc))
    cv_text = st.text_area("...ou cole o texto", key="cv_text", height=300)
with col_job:
    st.subheader("Vaga")
    job_text = st.text_area("Cole a descrição completa da vaga", key="job_text", height=380,
                            help='Mantenha títulos como "Requisitos" e "Diferenciais": eles definem o peso de cada habilidade.')

if st.button("Analisar", type="primary", disabled=not (cv_text.strip() and job_text.strip())):
    st.session_state["analisado"] = True
# o estado sobrevive aos recarregamentos (ex.: clicar em "Gerar sugestões")
if not (st.session_state.get("analisado") and cv_text.strip() and job_text.strip()):
    st.stop()

report = analyze(cv_text, job_text)

st.divider()
score_col, cov_col, req_col = st.columns(3)
score_col.metric("Nota de aderência", f"{report.score}/100")
cov_col.metric("Vocabulário da vaga no currículo", f"{report.keyword_coverage:.0%}")
req_total = len(report.required_skills)
req_col.metric("Obrigatórias atendidas", f"{len(report.matched_required)}/{req_total}" if req_total else "-")
st.progress(report.score / 100)


def chips(items: list[str], icon: str) -> str:
    return " ".join(f"`{icon} {item}`" for item in items) or "_nenhuma_"


left, right = st.columns(2)
with left:
    st.markdown("#### Habilidades obrigatórias")
    st.markdown(chips(report.matched_required, "✅") + " " + chips(report.missing_required, "❌"))
    st.markdown("#### Diferenciais")
    st.markdown(chips(report.matched_desired, "✅") + " " + chips(report.missing_desired, "➖"))
with right:
    st.markdown("#### Termos frequentes da vaga ausentes no currículo")
    st.markdown(chips(report.missing_keywords, "🔎"))
    st.markdown("#### Dicas")
    for tip in report.tips:
        st.markdown(f"- {tip}")

st.divider()
st.markdown("#### ✍️ Sugestões de reescrita com IA")
if not os.getenv("ANTHROPIC_API_KEY"):
    st.info(
        "Esta função usa a API do Claude e está desativada nesta instalação (sem chave configurada). "
        "Ela reescreve trechos do currículo com a linguagem da vaga e descarta automaticamente qualquer "
        "sugestão que invente uma habilidade que você não tem."
    )
elif st.button("Gerar sugestões"):
    from ats_match.llm import RefusalError, suggest_rewrites

    with st.spinner("Consultando o Claude..."):
        try:
            for s in suggest_rewrites(cv_text, job_text, report):
                st.markdown(f"**Antes:** {s.original}\n\n**Depois:** {s.rewritten}\n\n_{s.reason}_")
                st.divider()
        except RefusalError as exc:
            st.warning(str(exc))

st.caption("Projeto de portfólio de [Arthur Penedo](https://github.com/arthurpenedo) · código em "
           "[github.com/arthurpenedo/ats-match](https://github.com/arthurpenedo/ats-match)")
