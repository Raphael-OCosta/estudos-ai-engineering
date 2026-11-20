"""Gera praticar/capXX_*.ipynb (para você escrever) e resolvidos/capXX_*.ipynb (gabarito).

Uso (na raiz do curso):  .venv\\Scripts\\python.exe ferramentas\\gerar_cadernos.py
Não sobrescreve cadernos de praticar/ que já existem (para não apagar o que você escreveu).
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "comum"))
from exercicios import EXERCICIOS  # noqa: E402

SECOES = json.loads((RAIZ / "ferramentas" / "secoes.json").read_text(encoding="utf-8"))

TITULOS = {  # títulos mais naturais que os da tradução automática do sumário
    1: "Introdução: aplicações de IA com modelos de base", 2: "Entendendo os modelos de base",
    3: "Metodologia de avaliação", 4: "Avaliando sistemas de IA", 5: "Engenharia de prompt",
    6: "RAG e agentes", 7: "Ajuste fino (fine-tuning)", 8: "Engenharia de conjuntos de dados",
    9: "Otimização de inferência", 10: "Arquitetura de aplicações de IA e feedback do usuário",
}

PREPARACAO = ('import sys\n'
              'sys.path.insert(0, "../comum")  # onde ficam ia.py e os exercícios\n'
              'from ia import *               # cliente, perguntar(), conversar(), embeddings(), gasto() ...\n'
              'print("Pronto. Modelo padrão:", MODELO)')


def slug(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", t.lower()).strip("_")[:40].strip("_")


def md(s):
    return {"cell_type": "markdown", "metadata": {}, "source": s}


def code(s=""):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": s}


def caderno(cells):
    return {"cells": cells, "nbformat": 4, "nbformat_minor": 5,
            "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3 (.venv)", "language": "python"},
                         "language_info": {"name": "python"}}}


usados = set()
for n in range(1, 11):
    info = SECOES[str(n)]
    titulo = TITULOS[n]
    nome = f"cap{n:02d}_{slug(titulo)}.ipynb"
    ex_cap = [(i, e) for i, e in enumerate(EXERCICIOS) if e[0] == n]

    cab = (f"# Capítulo {n} — {titulo}\n\n"
           f"**Livro:** começa na página **{info['pag']}** do PDF.\n\n")
    pratica = [md(cab + "**Como usar:**\n"
                  "1. Rode a célula **Preparação** (`Shift+Enter`).\n"
                  "2. Leia cada seção no livro. Nas seções com **🧪 Exercício**, escreva o código na célula vazia.\n"
                  "3. Nas outras, use a célula **📝 Anotações** para resumir com suas palavras (dê dois cliques para editar).\n\n"
                  f"**Travou?** O gabarito está em `../resolvidos/{nome}`. "
                  "Material extra do autor (em inglês): `../chapter-summaries.md` e `../prompt-examples.md`."),
               md("## Preparação"), code(PREPARACAO)]
    gabarito = [md(cab + "📗 **Gabarito**: soluções dos exercícios do caderno de prática. "
                   "Tente sozinho antes de olhar. Cada chamada ao modelo custa centavos de centavo."),
                md("## Preparação"), code(PREPARACAO)]
    if n == 1:
        teste = 'print(perguntar("Diga olá em uma palavra."))\nprint(gasto())'
        pratica += [md("### ✅ Teste de conexão\nSe aparecer uma saudação e o gasto, está tudo certo."), code(teste)]
        gabarito += [md("### ✅ Teste de conexão"), code(teste)]

    for nivel, sec, pag in info["secoes"]:
        cabecalho = ("## " if nivel == 2 else "### ") + f"{sec} · PDF p. {pag}"
        pratica.append(md(cabecalho))
        exs = [(i, e) for i, e in ex_cap if sec.startswith(e[1])]
        if sec.startswith("Resumo"):
            pratica.append(md("📝 **Os 3 pontos mais importantes do capítulo, com suas palavras:**\n\n1. \n2. \n3. "))
            continue
        if not exs:
            pratica.append(md("📝 **Anotações:** _(dê dois cliques para escrever)_"))
            continue
        gabarito.append(md(cabecalho))
        for i, (_, _, nome_ex, enunciado, solucao) in exs:
            usados.add(i)
            pratica += [md(f"#### 🧪 Exercício: {nome_ex}\n\n{enunciado}"), code()]
            gabarito += [md(f"#### 🧪 Exercício: {nome_ex}\n\n{enunciado}"), code(solucao)]

    fim = "print(gasto())  # quanto esta sessão custou"
    pratica += [md("## 💰 Quanto gastei hoje"), code(fim), md("## 📝 Minhas anotações do capítulo\n\n- Aprendi:\n- Dúvidas:\n")]
    gabarito += [md("## 💰 Quanto gastei"), code(fim)]

    for pasta, cells, proteger in (("praticar", pratica, True), ("resolvidos", gabarito, False)):
        destino = RAIZ / pasta / nome
        destino.parent.mkdir(exist_ok=True)
        if proteger and destino.exists():
            print("já existe, mantido:", destino.relative_to(RAIZ))
            continue
        destino.write_text(json.dumps(caderno(cells), ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"cap{n:02d}: {len(ex_cap)} exercícios -> {nome}")

sobrando = [EXERCICIOS[i][2] for i in range(len(EXERCICIOS)) if i not in usados]
print("Exercícios sem seção correspondente:", sobrando or "nenhum")
