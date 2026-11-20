# 🧠 Estudos — *AI Engineering* (Chip Huyen) · 📖 em andamento

> **A melhor forma de estudar um livro técnico é ler e praticar ao mesmo tempo.**
> Leia uma seção, feche o livro e escreva o código com as próprias mãos. Só depois confira o gabarito.

Este repositório registra meu estudo de *AI Engineering: Building Applications with Foundation Models*.
O livro é conceitual e não tem exercícios, então escrevi **49 exercícios práticos** ligados às seções e páginas do PDF. Eles chamam **modelos reais** pelo OpenRouter.

## 🔁 O método

| Passo | O que fazer | Onde |
|---|---|---|
| 1. Ler | Ler a seção indicada | PDF do livro (página no caderno) |
| 2. Praticar | Escrever a solução do 🧪 exercício **sem olhar a resposta** | `praticar/capXX_*.ipynb` |
| 3. Conferir | Comparar com o gabarito | `resolvidos/capXX_*.ipynb` |
| 4. Resumir | Explicar com as próprias palavras nas células 📝 | `praticar/` |
| 5. Registrar | Commit + push | GitHub |

## 📚 Conteúdo (49 exercícios)

| Cap. | Tema | Exemplos |
|---|---|---|
| 1–2 | modelos de base | tokens, classificação, logprobs, temperatura, voto da maioria, saída JSON com pydantic |
| 3–4 | avaliação | entropia e perplexidade, correção funcional, similaridade, mapa de embeddings, **AI-as-a-judge**, viés de posição, *win rate*, TTFT, conjunto de avaliação |
| 5 | prompts | zero/few-shot, *system prompt*, encadeamento, chain-of-thought, versionamento, **prompt injection** |
| 6 | RAG e agentes | BM25 × semântica, RAG completo, chunking, *function calling*, laço de agente, memória |
| 7–9 | fine-tuning, dados, inferência | contas de memória, FP16/INT8, parâmetros do LoRA, deduplicação, dados sintéticos, JSONL, TTFT/TPOT, paralelismo |
| 10 | arquitetura | máscara de PII, roteador, cache exato e semântico, *logging*, sinais de feedback |

## 🛠️ Escolhas

- `comum/ia.py`: SDK da OpenAI apontado para o **OpenRouter**, com atalhos `perguntar`, `conversar`, `embeddings`, `similaridade` e `contar_tokens`, e controle de custo com `gasto()`.
- A chave fica **cifrada pelo Windows (DPAPI)** ou na variável `OPENROUTER_API_KEY`. Ela nunca vai para o código.
- `ferramentas/gerar_cadernos.py` gera os cadernos a partir de `ferramentas/secoes.json` (sumário do PDF) e de `comum/exercicios.py`.
- `ferramentas/testar_cadernos.py` roda o gabarito **offline**: 0 erros de código; as células que dependem do modelo são contadas à parte.
- [Guia de Estudos (PDF)](Guia_de_Estudos_AI_Engineering.pdf) para iniciantes, e um [prompt para recriar este ambiente](Prompt_ambiente_AI_Engineering.pdf) em outra máquina com o Claude Code.

## ⚖️ Direitos autorais

O livro **não** está neste repositório. Para estudar, use a sua própria cópia. O material de apoio da autora fica em [chiphuyen/aie-book](https://github.com/chiphuyen/aie-book) e não é republicado aqui.
Os exercícios, os cadernos, os scripts e o guia são autorais e estão sob licença [MIT](LICENSE).
