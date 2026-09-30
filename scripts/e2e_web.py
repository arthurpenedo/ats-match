"""Teste de fumaça da demo no navegador: carrega o exemplo, analisa e confere que a nota calculada
pelo Python no navegador (Pyodide) é a mesma do Python normal.

    python -m http.server -d site 8000 &
    python scripts/e2e_web.py http://localhost:8000/ [captura.png]
"""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
from ats_match import analyze  # noqa: E402


def main(url: str, captura: str | None = None) -> int:
    exemplos = RAIZ / "examples"
    esperado = analyze((exemplos / "curriculo.md").read_text(encoding="utf-8"),
                       (exemplos / "vaga.md").read_text(encoding="utf-8")).score
    with sync_playwright() as p:
        navegador = p.chromium.launch(channel=os.getenv("E2E_CHANNEL") or None)
        pagina = navegador.new_page(viewport={"width": 1280, "height": 1000})
        pagina.goto(url)
        pagina.get_by_role("button", name="Carregar exemplo").click(timeout=240_000)  # Pyodide + pacotes
        pagina.get_by_role("button", name="Analisar").click(timeout=60_000)
        pagina.get_by_text("Nota de aderência", exact=True).wait_for(timeout=60_000)
        nota = pagina.locator('[data-testid="stMetricValue"]').first.inner_text()
        if captura:
            pagina.mouse.wheel(0, 420)
            pagina.wait_for_timeout(800)
            pagina.screenshot(path=captura)
        navegador.close()
    print(f"navegador: {nota} · python: {esperado}/100")
    return 0 if nota == f"{esperado}/100" else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
