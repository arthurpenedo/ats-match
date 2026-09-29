"""Normalização e tokenização de texto em português e inglês."""

import re
import unicodedata
from collections import Counter, defaultdict

STOPWORDS = {
    # português
    "a", "o", "as", "os", "de", "da", "do", "das", "dos", "e", "em", "no", "na", "nos", "nas",
    "um", "uma", "uns", "umas", "para", "por", "com", "sem", "que", "se", "ao", "aos", "ou",
    "como", "mais", "menos", "ser", "ter", "sua", "seu", "suas", "seus", "nosso", "nossa",
    "voce", "sobre", "entre", "ate", "pelo", "pela", "pelos", "pelas", "ja", "tambem", "sao",
    "esta", "estao", "isso", "este", "essa", "esse", "muito", "bem", "etc", "area",
    "experiencia", "conhecimento", "conhecimentos", "vaga", "empresa", "time", "equipe",
    "atividades", "requisitos", "diferenciais", "responsabilidades", "trabalho", "anos",
    # inglês
    "the", "and", "or", "of", "to", "in", "for", "with", "on", "at", "by", "an", "is", "are",
    "be", "as", "from", "this", "that", "you", "we", "our", "your", "will", "years",
}

STEM_LENGTH = 6


def normalize(text: str) -> str:
    """Minúsculas, sem acentos e com espaços simples."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^\w\s\+\#\.\-/]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def stem(word: str) -> str:
    """Radical por truncamento: as flexões de uma palavra caem no mesmo radical.

    "automatizei", "automações" e "automação" viram "automa"; "desenvolvi" e
    "desenvolvimento" viram "desenv". É uma heurística simples e sem dependências;
    termos técnicos curtos (sql, python, aws) ficam intactos.
    """
    return word if len(word) <= STEM_LENGTH or not word.isalpha() else word[:STEM_LENGTH]


def _words(text: str) -> list[str]:
    tokens = (t.strip(".-") for t in re.findall(r"[a-z0-9\+\#][a-z0-9\+\#\.\-]*", normalize(text)))
    return [t for t in tokens if t and t not in STOPWORDS and len(t) > 1]


def tokenize(text: str) -> list[str]:
    return [stem(w) for w in _words(text)]


def top_terms(text: str, n: int = 25) -> list[tuple[str, str]]:
    """Termos mais frequentes do texto, como pares (radical, forma mais comum no texto).

    O radical é usado para comparar; a forma original é a que aparece para o usuário.
    """
    stems: Counter[str] = Counter()
    surfaces: defaultdict[str, Counter[str]] = defaultdict(Counter)
    for word in _words(text):
        s = stem(word)
        stems[s] += 1
        surfaces[s][word] += 1
    return [(s, surfaces[s].most_common(1)[0][0]) for s, _ in stems.most_common(n)]
