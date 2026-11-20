# Prompt — ambiente de estudos do livro *AI Engineering* (Chip Huyen)

## Antes de começar (para você, colega)

1. Instale o **VS Code**, o **Git** e o **Claude Code** (app desktop, aba Code, ou CLI).
2. Tenha a **sua cópia do livro em PDF** salva no notebook.
3. Crie uma conta no **OpenRouter** (openrouter.ai), coloque alguns dólares de crédito (US$ 5 duram muito tempo) e gere uma **API key**. **Não cole a chave no chat:** o próprio ambiente vai pedir para você gravá-la de forma segura.
4. No Claude Code, anexe o PDF com `@` e o caminho do arquivo, cole o prompt abaixo e envie.

---

## Prompt (copie daqui até o fim)

Sou iniciante (nível 0) e estudo cerca de 60 minutos por dia. Quero montar no meu notebook Windows um ambiente de estudos para o livro anexo, *AI Engineering* (Chip Huyen), usando VS Code + Jupyter. Faça tudo por mim e me explique cada passo como se eu nunca tivesse programado.

**1. Mapa do livro.** Use `pymupdf` (`get_toc()`) para listar capítulos e seções (níveis 2 e 3) com a página do PDF em que cada um começa. Salve o resultado em `ferramentas/secoes.json`. Se o PDF for uma tradução automática, os títulos podem sair estranhos ("TRAPO" = RAG, "Engenharia Rápida" = Prompt Engineering); nos cadernos, use o termo técnico original.

**2. Pasta e repositório.** Clone https://github.com/chiphuyen/aie-book em `C:\estudos\ai_engineering`. Esse repositório tem só material de referência e nenhum exercício. Coloque os meus arquivos locais em `.git/info/exclude` para eles não entrarem no git.

**3. Python.** Se eu não tiver o Python 3.12 do **python.org**, instale (`winget install Python.Python.3.12`). Crie a `.venv` com `python -m venv .venv` usando esse Python. **Não** use o Python gerenciado pelo `uv`, porque o kernel do VS Code quebra com ele; o `uv` pode ser usado só para instalar as bibliotecas. Garanta que `pip` e `ipykernel` fiquem dentro da `.venv`. Crie um `requirements-estudos.txt` com: ipykernel, pip, openai, tiktoken, numpy, pandas, matplotlib, pydantic, jsonschema, rank-bm25, pypdf, scikit-learn, nbclient, nbformat.

**4. Chave do OpenRouter (segurança).** O acesso aos modelos é pelo OpenRouter, que tem uma API compatível com a da OpenAI (`base_url = https://openrouter.ai/api/v1`). A chave **nunca** deve ficar em arquivo de texto nem no código, e você **não** deve pedi-la no chat. Crie um `ferramentas/salvar_chave.ps1` para **eu** rodar. Ele deve:
- pedir a chave com `Read-Host -AsSecureString`;
- gravar o resultado de `ConvertFrom-SecureString` (cifrado por DPAPI, legível só pelo meu usuário do Windows) em `%USERPROFILE%\.secrets\openrouter.dpapi`.

**5. `comum/ia.py`, o módulo que todos os cadernos importam.**
- Cliente OpenAI apontando para o OpenRouter.
- Lê a chave da variável `OPENROUTER_API_KEY` ou do arquivo DPAPI: o arquivo contém hex; converta para bytes, decifre com `CryptUnprotectData` via `ctypes` e leia o texto como UTF-16LE.
- A variável `IA_BASE_URL` troca o endpoint (para os testes offline).
- Modelos: `openai/gpt-4o-mini` (padrão), `openai/gpt-4o` (forte e juiz) e `openai/text-embedding-3-small`.
- Funções: `conversar`, `perguntar`, `embeddings`, `similaridade` (cosseno), `contar_tokens` (tiktoken `o200k_base`) e `gasto()`, que mostra chamadas, tokens e custo em US$.

**6. Exercícios.** O livro é conceitual e não traz código. Escreva `comum/exercicios.py` com cerca de 50 exercícios práticos no formato (capítulo, prefixo do título da seção, título, enunciado em Markdown, solução), cobrindo os 10 capítulos:
- **Modelos e saídas:** tokens, logprobs, temperatura, voto da maioria, saída estruturada com JSON + pydantic, entropia e perplexidade.
- **Avaliação:** métricas de similaridade, embeddings com mapa de calor, AI-as-a-judge e viés de posição, win rate, conjunto de avaliação.
- **Prompts:** zero/few-shot, system prompt, encadeamento de prompts, chain-of-thought, versionamento de prompts, prompt injection.
- **RAG e agentes:** BM25 × busca semântica, RAG completo, chunking, function calling, loop de agente, resumo de memória.
- **Fine-tuning e dados:** contas de memória, FP16 e quantização INT8, contagem de parâmetros do LoRA, deduplicação, dados sintéticos, JSONL.
- **Inferência e produção:** TTFT/TPOT, requisições paralelas, cache exato e semântico, roteador, mascaramento de PII, logging, sinais de feedback.

Use só exemplos inventados, nada de dados reais de empresa.

**7. Cadernos.** Crie `ferramentas/gerar_cadernos.py`, que gera dois conjuntos:
- `praticar/capXX_<titulo>.ipynb`: células de código **vazias** para eu digitar;
- `resolvidos/capXX_<titulo>.ipynb`: o gabarito, para consultar.

A estrutura de cada caderno:
- cabeçalho;
- célula "Preparação" com `sys.path.insert(0, "../comum")` e `from ia import *`;
- só no cap. 1, uma célula **✅ Teste de conexão**;
- cada seção do livro como `## Título · PDF p. N`;
- seção sem exercício: uma célula 📝 Anotações;
- seção com exercício: 🧪 enunciado e uma célula de código vazia;
- seções "Resumo": "3 pontos principais";
- no fim, 💰 `gasto()` e anotações finais.

O gerador **nunca** deve sobrescrever um `praticar/` que já exista.

**8. Testes.** `ferramentas/testar_cadernos.py` roda os cadernos de `resolvidos/` com nbclient **offline**: chave falsa e `IA_BASE_URL=http://127.0.0.1:9/v1`. Ele conta à parte os erros de rede (`APIConnectionError`, `AuthenticationError`, `APITimeoutError`) e só aprova com **0 erros de código**. Apague os arquivos que os testes criarem. Quem faz o teste real de conexão sou **eu**, na célula ✅ do cap. 1. Não decifre a minha chave.

**9. VS Code.** Crie `.vscode/settings.json` na pasta com:
- `python.defaultInterpreterPath` = `${workspaceFolder}\.venv\Scripts\python.exe`;
- `jupyter.notebookFileRoot` = `${fileDirname}`.

Instale as extensões Python e Jupyter. Se eu já tiver um arquivo `.code-workspace` com meus projetos, adicione a pasta nele (com backup antes) em vez de criar outro. Se não tiver, crie `C:\estudos\Estudos.code-workspace` e um atalho na Área de Trabalho.

**10. Guia em PDF (não em Markdown).** Escreva `guia_pdf/guia.html` e converta para `Guia_de_Estudos_AI_Engineering.pdf` com o Edge headless (`msedge --headless=new --no-pdf-header-footer --print-to-pdf=...`). São cerca de 10 páginas, bonitas e para iniciante:
1. capa;
2. o que é cada coisa (VS Code, Jupyter, kernel, venv, OpenRouter, chave);
3. vocabulário;
4. Parte 1, a primeira vez, clique a clique: abrir a pasta, dar Trust, escolher o kernel `.venv`, salvar a chave com `salvar_chave.ps1`, rodar a Preparação e o teste de conexão;
5. tabela de erros da Parte 1: chave ausente, 401 (chave errada), 402 (sem crédito), APIConnectionError (rede);
6. Parte 2, a rotina de 60 minutos (cerca de 15 páginas por sessão), digitando em `praticar/` e consultando `resolvidos/`;
7. mapa capítulo → página → caderno → número de exercícios;
8. um exemplo completo;
9. as ferramentas do `ia.py` e o custo, com o aviso de não mandar dados da empresa;
10. atalhos e erros comuns: NameError → rodar as células de cima; kernel errado; Reload Window.

Confira o layout gerando miniaturas das páginas.

**11. No fim**, abra o guia e me diga exatamente qual é o primeiro passo que eu devo dar.
