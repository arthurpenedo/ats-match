"""CLI: `ats-match curriculo.pdf vaga.md [--sugerir] [--json]` (PDF, DOCX, MD ou TXT)."""

import argparse
import sys
from pathlib import Path

from .extract import ExtractionError, read_file
from .matcher import analyze


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compara currículo × vaga como um ATS.")
    parser.add_argument("curriculo", type=Path)
    parser.add_argument("vaga", type=Path)
    parser.add_argument("--sugerir", action="store_true", help="gera sugestões de reescrita com Claude")
    parser.add_argument("--json", action="store_true", help="imprime o relatório em JSON")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # acentos corretos no terminal do Windows

    try:
        resume = read_file(args.curriculo)
        job = read_file(args.vaga)
    except ExtractionError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2
    report = analyze(resume, job)

    if args.json:
        print(report.model_dump_json(indent=2))
    else:
        print(f"\nNota de aderência: {report.score}/100\n")
        print(f"Obrigatórias atendidas: {', '.join(report.matched_required) or '-'}")
        print(f"Obrigatórias faltando:  {', '.join(report.missing_required) or '-'}")
        print(f"Diferenciais atendidos: {', '.join(report.matched_desired) or '-'}")
        print(f"Cobertura de vocabulário da vaga: {report.keyword_coverage:.0%}")
        print(f"Termos da vaga ausentes: {', '.join(report.missing_keywords) or '-'}\n")
        for tip in report.tips:
            print(f"- {tip}")

    if args.sugerir:
        from .llm import suggest_rewrites

        print("\nSugestões de reescrita:\n")
        for s in suggest_rewrites(resume, job, report):
            print(f"  ANTES:  {s.original}\n  DEPOIS: {s.rewritten}\n  POR QUÊ: {s.reason}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
