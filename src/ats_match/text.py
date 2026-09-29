"""Normalização e tokenização de texto em português e inglês."""

import re
import unicodedata
from collections import Counter

STOPWORDS = {
    # português
    "a", "o", "as", "os", "de", "da", "do", "das", "dos", "e", "em", "no", "na", "nos", "nas",
    "um", "uma", "uns", "umas", "para", "por", "com", "sem", "que", "se", "ao", "aos", "ou",
    "como", "mais", "menos", "ser", "ter", "sua", "seu", "suas", "seus", "nosso", "nossa",
    "voce", "sobre", "entre", "ate", "pelo", "pela", "pelos", "pelas", "ja", "tambem", "sao",
    "esta", "estao", "isso", "este", "esta", "essa", "esse", "muito", "bem", "etc", "area",
    "experiencia", "conhecimento", "conhecimentos", "vaga", "empresa", "time", "equipe",
    "atividades", "requisitos", "diferenciais", "responsabilidades", "trabalho", "anos",
    # inglês
    "the", "and", "or", "of", "to", "in", "for", "with", "on", "at", "by", "an", "is", "are",
    "be", "as", "from", "this", "that", "you", "we", "our", "your", "will", "years",
}


def normalize(text: str) -> str:
    """Minúsculas, sem acentos e com espaços simples."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^\w\s\+\#\.\-/]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9\+\#][a-z0-9\+\#\.\-]*", normalize(text))
    return [t.strip(".-") for t in tokens if t.strip(".-") and t.strip(".-") not in STOPWORDS and len(t.strip(".-")) > 1]


def top_terms(text: str, n: int = 25) -> list[str]:
    """Termos mais frequentes (sem stopwords), usados como proxy de palavras-chave da vaga."""
    counts = Counter(tokenize(text))
    return [term for term, _ in counts.most_common(n)]
