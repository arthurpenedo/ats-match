# ats-match

[![CI](https://github.com/arthurpenedo/ats-match/actions/workflows/ci.yml/badge.svg)](https://github.com/arthurpenedo/ats-match/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

> Compara um currículo com uma vaga do jeito que um **ATS** (Gupy, Greenhouse, Workday) compara, mostra o que está faltando e sugere reescritas **honestas** com a ajuda do Claude.

## O problema

No Brasil, a maioria das vagas passa primeiro por um ATS. Ele extrai o texto do currículo, procura as habilidades e palavras-chave do anúncio e **ranqueia** os candidatos. Um currículo bom, mas escrito com um vocabulário diferente do anúncio, cai para o fim da fila, e às vezes nenhuma pessoa chega a ler.

O `ats-match` faz essa leitura antes do envio e responde três perguntas:

1. **Qual a minha aderência a esta vaga?** Nota de 0 a 100.
2. **O que está faltando?** Habilidades obrigatórias, diferenciais e termos do anúncio.
3. **Como reescrever sem mentir?** Sugestões geradas por LLM, com uma trava que **descarta qualquer sugestão que invente uma habilidade** ausente do currículo.

## Demo

```text
$ ats-match examples/curriculo.md examples/vaga.md

Nota de aderência: 76/100

Obrigatórias atendidas: Atendimento ao cliente, Automação de processos, Git, LLMs, Prompt engineering, Python, SQL
Obrigatórias faltando:  APIs REST
Diferenciais atendidos: AWS, Inglês, Power BI
Cobertura de vocabulário da vaga: 48%
Termos da vaga ausentes: llms, junior, desenvolver, automacoes, apis, rest, criar, testar, assistentes, baseados

- Se você TEM experiência com APIs REST, deixe isso explícito com o mesmo termo usado na vaga. Se não tem, não invente: destaque experiências próximas e reais.
- Menos da metade do vocabulário da vaga aparece no currículo. Reescreva as descrições de experiência usando os termos do anúncio (sem mudar os fatos).
```

## Como funciona

```
currículo ─┐                        ┌─► nota 0-100
           ├─► normalização ─► ─────┼─► habilidades atendidas / faltando
vaga ──────┘   (acentos, stopwords) │   (obrigatórias × diferenciais)
                                    └─► vocabulário do anúncio ausente
                                                  │
                                    (opcional)    ▼
                              Claude sugere reescritas ─► validação anti-invenção ─► sugestões
```

- **Taxonomia de habilidades** (`skills.py`): cada habilidade tem sinônimos que os ATS tratam como equivalentes (ex.: *Athena* → AWS, *IA generativa* → LLMs), com casamento por palavra inteira (*ml* não casa dentro de *html*).
- **Seções da vaga** (`matcher.py`): o que vem sob "Diferenciais"/"Desejável" pesa metade do que é obrigatório.
- **Nota:** 75% cobertura ponderada de habilidades + 25% cobertura dos 25 termos mais frequentes do anúncio.
- **Camada de IA** (`llm.py`): Claude (`claude-opus-5-5`) com **saída estruturada em JSON Schema**, tratamento de recusa e fallback no servidor. Toda sugestão passa por `validate_suggestions`.

### Decisões técnicas

- **Núcleo determinístico, IA opcional.** A nota é explicável e reproduzível, sem custo de API e sem variação entre execuções. O LLM entra só onde agrega: reescrever texto.
- **A trava anti-invenção é código, não prompt.** O prompt pede para não inventar, mas quem garante é a validação: se a sugestão cita uma habilidade que não está no currículo, ela é descartada.
- **Testes sem chave de API.** O cliente do Claude é injetável, e os testes usam um cliente falso.

## Como rodar

```bash
git clone https://github.com/arthurpenedo/ats-match && cd ats-match
pip install -e ".[dev]"

ats-match examples/curriculo.md examples/vaga.md          # relatório
ats-match examples/curriculo.md examples/vaga.md --json   # JSON

# sugestões com IA (precisa de ANTHROPIC_API_KEY)
ats-match examples/curriculo.md examples/vaga.md --sugerir

# API
uvicorn ats_match.api:app --reload   # POST /match e POST /suggest

pytest -q
```

## Limitações conhecidas

- Sem lematização: "automatizei" e "automações" contam como termos diferentes.
- A taxonomia cobre principalmente vagas de dados, IA e automação.
- Não lê PDF ainda (entrada em texto/Markdown).
- Não distingue nível de proficiência (ex.: inglês intermediário × avançado).

## Próximos passos

- [ ] Leitura de PDF e DOCX
- [ ] Lematização em português
- [ ] Interface web (Streamlit) com comparação antes/depois
- [ ] Ranking de várias vagas para o mesmo currículo

---

Feito por [Arthur Penedo](https://github.com/arthurpenedo) · [LinkedIn](https://www.linkedin.com/in/arthuralves-penedo)
