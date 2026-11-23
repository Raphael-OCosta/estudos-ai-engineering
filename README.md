# Estudos — *AI Engineering* (Chip Huyen) · trilha prática

> **A melhor forma de estudar um livro técnico é ler e praticar ao mesmo tempo.**
> Nesta versão a prática vem primeiro: cada capítulo é uma **missão** curta. Você lê só o essencial e constrói uma peça de um sistema real.

Este repositório registra meu estudo de *AI Engineering: Building Applications with Foundation Models* (edição em inglês).
Ao longo dos 10 capítulos, você constrói, módulo a módulo, o **assistente de suporte da Nimbus**, uma empresa fictícia de software. O assistente tem:

- avaliação automática;
- prompts versionados e defesas contra ataques;
- RAG com busca híbrida;
- um agente com ferramentas;
- cache, roteador de modelos, guardrails e monitoramento.

## Como cada caderno funciona

1. **Missão**: o que você vai construir e por quê, em poucas linhas.
2. **Leitura essencial**: só as seções que importam, com a página do PDF em inglês (opcional).
3. **Passos práticos**: uma explicação curta e uma célula vazia para você digitar. Os módulos do projeto já vêm com a linha `%%writefile` pronta.
4. **Gabarito** em `resolvidos/`, com o mesmo passo a passo pronto.

## A trilha (106 passos)

| Cap. | Missão | Você constrói |
|---|---|---|
| 1 | Primeira aplicação de IA | latência, custo mensal, matriz de viabilidade de casos de uso, `nucleo.py` |
| 2 | Tokens, amostragem e saídas estruturadas | softmax com temperatura, top-k/top-p à mão, logprobs, autoconsistência, `estruturado.py` (pydantic) |
| 3 | Como medir se a IA acertou | entropia, perplexidade, correção funcional, F1, n-gramas, embeddings, juiz com rubrica, viés de posição, Elo, `metricas.py`, `juiz.py` |
| 4 | Avaliar o sistema e escolher o modelo | verificadores de instrução, diretriz, bootstrap, fatias, nota por dólar, `avaliacao.py` |
| 5 | Prompts e defesas | zero × few-shot, agulha no palheiro, decomposição, raciocínio, injeção e vazamento de prompt, `prompts.py`, `defesas.py` |
| 6 | RAG e agentes | pedaços, BM25, embeddings, RRF, recall@k/MRR, reescrita de consulta, `rag.py`, agente com ferramentas, memória |
| 7 | Ajuste fino sem GPU | memória de inferência e treino, bf16, quantização int8, **LoRA treinado em NumPy**, fusão de modelos, JSONL de treino |
| 8 | Engenharia de dados | inspeção, deduplicação com MinHash, filtros e PII, cobertura, dados sintéticos verificados por juiz, destilação, `dados_treino.py` |
| 9 | Inferência rápida e barata | TTFT/TPOT, percentis, concorrência, cache exato e semântico, KV cache, roofline, decodificação especulativa, `cache.py` |
| 10 | Arquitetura completa e feedback | guardrails, roteador, `assistente.py` completo, painel de monitoramento, feedback explícito/implícito, comparação final |

## Como usar

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-estudos.txt
.venv\Scripts\python.exe ferramentas\testar_cadernos.py    # opcional: roda o gabarito no modo simulado
```

- Os modelos são chamados pelo **OpenRouter** (`comum/ia.py`). A chave fica cifrada pelo Windows (DPAPI) ou na variável `OPENROUTER_API_KEY` e nunca vai para o código.
- **Modo simulado** (`IA_FAKE=1`): respostas falsas, mas no mesmo formato das reais (logprobs, várias amostras, streaming, JSON e ferramentas). Serve para testar sem custo; o gabarito é testado assim.
- Os dados da Nimbus (documentos, perguntas de avaliação, chamados) são fictícios e estão em `comum/dados.py`.
- O [Guia de Estudos (PDF)](Guia_de_Estudos.pdf) explica o passo a passo.
- A versão anterior, feita sobre a tradução em português, está preservada em `versao_anterior_pt/`, com o progresso do estudo.

## Direitos autorais

O livro **não** está neste repositório. Para estudar, use a sua própria cópia. O material de apoio da autora fica em [chiphuyen/aie-book](https://github.com/chiphuyen/aie-book) e não é republicado aqui.
As missões, os cadernos, os dados fictícios, os scripts e o guia são autorais e estão sob licença [MIT](LICENSE).
