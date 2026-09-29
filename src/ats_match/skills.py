"""Taxonomia de habilidades: nome canônico -> variações que os ATS tratam como equivalentes."""

import re

from .text import normalize

SKILLS: dict[str, list[str]] = {
    "Python": ["python"],
    "SQL": ["sql", "t-sql", "pl/sql", "consultas sql"],
    "JavaScript": ["javascript", "js", "node.js", "nodejs", "node"],
    "TypeScript": ["typescript"],
    "React": ["react", "react.js", "reactjs"],
    "APIs REST": ["api rest", "apis rest", "rest api", "restful", "apis"],
    "FastAPI": ["fastapi"],
    "Git": ["git", "github", "gitlab"],
    "Docker": ["docker", "containers"],
    "AWS": ["aws", "amazon web services", "athena", "quicksight", "s3", "lambda"],
    "Azure": ["azure"],
    "GCP": ["gcp", "google cloud", "bigquery"],
    "Power BI": ["power bi", "powerbi"],
    "Power Automate": ["power automate", "power platform"],
    "Alteryx": ["alteryx"],
    "Excel": ["excel", "planilhas"],
    "LLMs": ["llm", "llms", "large language model", "modelos de linguagem", "ia generativa",
             "generative ai", "genai", "gpt", "claude", "gemini"],
    "Prompt engineering": ["prompt engineering", "engenharia de prompt", "prompts", "testes de prompt"],
    "RAG": ["rag", "retrieval augmented generation", "retrieval-augmented"],
    "Agentes de IA": ["agentic", "ai agents", "agentes de ia", "agentes autonomos", "tool use"],
    "Machine Learning": ["machine learning", "aprendizado de maquina", "ml", "scikit-learn", "sklearn"],
    "NLP": ["nlp", "processamento de linguagem natural", "natural language processing"],
    "Automação de processos": ["automacao", "automation", "rpa", "automatizacao"],
    "Microsoft Copilot": ["copilot", "microsoft copilot"],
    "n8n": ["n8n"],
    "Análise de dados": ["analise de dados", "data analysis", "analytics", "analise de indicadores"],
    "Pandas": ["pandas"],
    "Métodos ágeis": ["scrum", "agile", "kanban", "metodos ageis"],
    "Inglês": ["ingles", "english"],
    "Atendimento ao cliente": ["atendimento", "customer service", "cx", "customer experience"],
    "Monitoria de qualidade": ["monitoria", "monitoramento", "qualidade de atendimento", "quality assurance"],
}

_PATTERNS = {
    skill: [re.compile(rf"(?<![\w]){re.escape(normalize(v))}(?![\w])") for v in variants]
    for skill, variants in SKILLS.items()
}


def find_skills(text: str) -> set[str]:
    """Retorna as habilidades canônicas mencionadas no texto (casamento por termo inteiro)."""
    norm = normalize(text)
    return {skill for skill, patterns in _PATTERNS.items() if any(p.search(norm) for p in patterns)}
