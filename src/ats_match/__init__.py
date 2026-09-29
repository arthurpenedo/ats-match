"""ats-match: análise de aderência currículo × vaga no estilo de um ATS."""

from .matcher import MatchReport, analyze

__all__ = ["MatchReport", "analyze"]
__version__ = "0.1.0"
