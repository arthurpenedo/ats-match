"""Gera a demo estática: o app Streamlit rodando inteiro no navegador com o stlite (Pyodide/WebAssembly).

    python scripts/build_web.py site

Não há servidor: o GitHub Pages entrega os arquivos .py e o navegador executa o Python.
O currículo enviado nunca sai do computador de quem usa a demo. A função de reescrita com IA
fica desativada ali (precisaria de chave de API), exatamente como numa instalação sem chave.
"""

import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
STLITE = "1.9.2"
# só o necessário para a análise; llm.py (anthropic), api.py e cli.py não rodam no navegador
MODULOS = ["__init__.py", "matcher.py", "skills.py", "text.py", "extract.py"]
REQUISITOS = ["pydantic", "pypdf", "python-docx"]

HTML = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
<title>ats-match · currículo × vaga</title>
<meta name="description" content="Veja seu currículo como um ATS vê: nota de aderência à vaga, habilidades que faltam e dicas. Roda no seu navegador.">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@stlite/browser@{versao}/build/stlite.css">
</head>
<body>
<div id="root"></div>
<noscript>Esta demo precisa de JavaScript: ela roda o Python no seu navegador.</noscript>
<script type="module">
import {{ mount }} from "https://cdn.jsdelivr.net/npm/@stlite/browser@{versao}/build/stlite.js";
mount({{
  requirements: {requisitos},
  entrypoint: "streamlit_app.py",
  files: {{
{arquivos}
  }},
  streamlitConfig: {{ "client.toolbarMode": "viewer" }},
}}, document.getElementById("root"));
</script>
</body>
</html>
"""


def build(destino: Path) -> Path:
    if destino.exists():
        shutil.rmtree(destino)
    copias = {"streamlit_app.py": RAIZ / "streamlit_app.py"}
    copias |= {f"ats_match/{m}": RAIZ / "src" / "ats_match" / m for m in MODULOS}
    copias |= {f"examples/{p.name}": p for p in sorted((RAIZ / "examples").glob("*.md"))}
    for rel, origem in copias.items():
        (destino / "app" / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origem, destino / "app" / rel)
    arquivos = ",\n".join(f'    "{rel}": {{ url: "./app/{rel}" }}' for rel in copias)
    requisitos = "[" + ", ".join(f'"{r}"' for r in REQUISITOS) + "]"
    (destino / "index.html").write_text(
        HTML.format(versao=STLITE, requisitos=requisitos, arquivos=arquivos), encoding="utf-8")
    return destino / "index.html"


if __name__ == "__main__":
    print(build(Path(sys.argv[1] if len(sys.argv) > 1 else "site")))
