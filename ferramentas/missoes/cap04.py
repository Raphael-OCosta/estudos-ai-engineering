TITULO = "Avaliando o sistema e escolhendo o modelo"
MISSAO = (
    "Transformar as métricas do capítulo 3 num **pipeline de avaliação** do assistente: um conjunto de perguntas com "
    "referência, uma diretriz com critérios, verificadores automáticos de instruções, custo e latência por modelo, "
    "intervalo de confiança e análise por fatias. No fim, você escolhe o modelo com dados, não com opinião."
)
ENTREGA = "o módulo `PKG/avaliacao.py`, que avalia qualquer função `responder` e devolve uma tabela com nota, F1, similaridade, latência e custo."
LEITURA = [("Evaluation Criteria (Instruction-Following, Cost and Latency)", 184), ("Model Selection Workflow", 203),
           ("Design Your Evaluation Pipeline", 224)]

PASSOS = [
    ("texto",
     "## Ideia em 30 segundos\n"
     "Avaliar um modelo solto não basta: o que importa é o **sistema** (prompt + contexto + modelo + regras) no "
     "**seu** caso de uso. O caminho é:\n"
     "1. escrever o que é uma boa resposta (diretriz);\n"
     "2. montar um conjunto de avaliação parecido com o uso real;\n"
     "3. medir com vários métodos;\n"
     "4. olhar os resultados por fatias e com margem de erro.\n\n"
     "Rankings públicos ajudam só a fazer a primeira peneira."),

    ("tarefa",
     "**Verificadores de instrução.** Escreva 4 funções que conferem uma resposta e devolvem `True/False`: "
     "`max_palavras(t, n)`, `contem(t, termo)`, `eh_json(t)` e `termina_com_pergunta(t)`. Peça ao modelo: "
     "\"Em no máximo 25 palavras, explique o plano Grátis da Nimbus, cite 'CSV' e termine com uma pergunta ao "
     "cliente.\" Passe a resposta pelos verificadores que valem para esse pedido.",
     r'''def max_palavras(t, n):
    return len(t.split()) <= n

def contem(t, termo):
    return termo.lower() in t.lower()

def eh_json(t):
    try:
        json.loads(t)
        return True
    except (ValueError, TypeError):
        return False

def termina_com_pergunta(t):
    return t.strip().endswith("?")

resp = perguntar("Em no máximo 25 palavras, explique o plano Grátis da Nimbus, cite 'CSV' e termine com uma "
                 "pergunta ao cliente.")
print(resp)
print({"<=25 palavras": max_palavras(resp, 25), "cita CSV": contem(resp, "CSV"),
       "termina com ?": termina_com_pergunta(resp)})'''),

    ("tarefa",
     "**Custo e latência por modelo.** Para 3 perguntas de `PERGUNTAS`, rode `responder` com `MODELO` e com "
     "`MODELO_FORTE`. Monte uma tabela com a média de latência e de tokens por modelo e um custo estimado (use os "
     "preços do capítulo 1).",
     r'''from PKG.nucleo import responder
precos = {MODELO: (0.15, 0.60), MODELO_FORTE: (2.50, 10.00)}
linhas = []
for modelo in (MODELO, MODELO_FORTE):
    for p in PERGUNTAS[:3]:
        r = responder(p["pergunta"], modelo=modelo)
        pin, pout = precos[modelo]
        linhas.append({"modelo": modelo, "latencia_s": r["latencia_s"],
                       "custo_usd": r["tokens_in"] / 1e6 * pin + r["tokens_out"] / 1e6 * pout})
pd.DataFrame(linhas).groupby("modelo").mean()'''),

    ("tarefa",
     "**Diretriz de avaliação.** Escreva a diretriz do assistente como um dicionário de critérios, cada um com "
     "`descricao` e `peso` (pesos somam 1): por exemplo correção, uso só da documentação, tom e concisão. Escreva "
     "`nota_final(notas)`, que recebe notas de 1 a 5 por critério e devolve a média ponderada.",
     r'''DIRETRIZ = {
    "correcao": {"descricao": "a informação bate com a documentação da Nimbus", "peso": 0.5},
    "fundamentacao": {"descricao": "não inventa nada que não esteja na documentação", "peso": 0.2},
    "tom": {"descricao": "educado e claro, em português", "peso": 0.15},
    "concisao": {"descricao": "no máximo 3 frases", "peso": 0.15},
}

def nota_final(notas):
    return sum(DIRETRIZ[c]["peso"] * notas[c] for c in DIRETRIZ)

print(nota_final({"correcao": 5, "fundamentacao": 4, "tom": 5, "concisao": 3}))'''),

    ("arquivo",
     "**Pipeline de avaliação.** Escreva `avaliacao.py` com `avaliar(responder, perguntas, juiz=True)`. Para cada item "
     "de `perguntas`, chama `responder(pergunta)` (que devolve um dict com `texto`, `latencia_s`, `tokens_in`, "
     "`tokens_out` e `modelo`) e calcula: `f1`, `semantica`, `nota_juiz` (se `juiz=True`), latência e custo "
     "(dicionário `PRECOS` por modelo). Devolve um `DataFrame` que mantém também o `doc` de cada pergunta. Inclua "
     "`resumo(df)`, com as médias, a % de notas >= 4 e a latência p90.",
     "avaliacao.py",
     r'''"""Pipeline de avaliação: roda um sistema num conjunto de perguntas e mede tudo."""
import numpy as np
import pandas as pd

from .juiz import julgar
from .metricas import f1_tokens, similaridade_semantica

PRECOS = {"openai/gpt-4o-mini": (0.15, 0.60), "openai/gpt-4o": (2.50, 10.00)}   # US$ por 1M tokens


def avaliar(responder, perguntas: list[dict], juiz: bool = True) -> pd.DataFrame:
    linhas = []
    for item in perguntas:
        r = responder(item["pergunta"])
        pin, pout = PRECOS.get(r.get("modelo"), (0.0, 0.0))
        linha = {
            "pergunta": item["pergunta"],
            "doc": item.get("doc"),
            "resposta": r["texto"],
            "f1": f1_tokens(r["texto"], item["referencia"]),
            "semantica": similaridade_semantica(r["texto"], item["referencia"]),
            "latencia_s": r.get("latencia_s", 0.0),
            "custo_usd": r.get("tokens_in", 0) / 1e6 * pin + r.get("tokens_out", 0) / 1e6 * pout,
        }
        if juiz:
            linha["nota_juiz"] = julgar(item["pergunta"], r["texto"], item["referencia"])["nota"]
        linhas.append(linha)
    return pd.DataFrame(linhas)


def resumo(df: pd.DataFrame) -> pd.Series:
    s = {"f1": df.f1.mean(), "semantica": df.semantica.mean(),
         "latencia_p90_s": float(np.percentile(df.latencia_s, 90)), "custo_total_usd": df.custo_usd.sum()}
    if "nota_juiz" in df:
        s["nota_media"] = df.nota_juiz.mean()
        s["pct_nota_4+"] = (df.nota_juiz >= 4).mean()
    return pd.Series(s).round(4)
'''),

    ("tarefa",
     "**Linha de base.** Avalie o `nucleo.responder` (sem documentação, só o modelo) nas 8 primeiras perguntas. "
     "Mostre a tabela e o `resumo`. Guarde o resultado em `../saidas/base_cap04.csv`: você vai comparar com o RAG no "
     "capítulo 6.",
     r'''from PKG.avaliacao import avaliar, resumo
from PKG.nucleo import responder
base = avaliar(responder, PERGUNTAS[:8])
base.to_csv("../saidas/base_cap04.csv", index=False)
display(base[["pergunta", "resposta", "f1", "semantica", "nota_juiz"]])
resumo(base)'''),

    ("tarefa",
     "**Margem de erro (bootstrap).** Com poucas perguntas, a média engana. Faça 2.000 reamostragens com reposição "
     "das notas do juiz e mostre o intervalo de 95% (percentis 2,5 e 97,5) da média.",
     r'''rng = np.random.default_rng(0)
notas = base.nota_juiz.to_numpy()
medias = [rng.choice(notas, size=len(notas), replace=True).mean() for _ in range(2000)]
print(f"média {notas.mean():.2f} | IC 95%: {np.percentile(medias, 2.5):.2f} a {np.percentile(medias, 97.5):.2f}")'''),

    ("tarefa",
     "**Fatias.** Agrupe o resultado por `doc` (assunto da pergunta) e veja em qual assunto o sistema vai pior. "
     "É ali que vale investir primeiro.",
     r'''base.groupby("doc")[["f1", "semantica", "nota_juiz"]].mean().sort_values("nota_juiz")'''),

    ("tarefa",
     "**Seleção de modelo.** Avalie as mesmas 8 perguntas com `MODELO_FORTE` (use `lambda p: responder(p, "
     "modelo=MODELO_FORTE)`). Compare os dois resumos lado a lado e calcule **nota média por dólar**. Qual você "
     "escolheria para o suporte, e por quê?",
     r'''forte = avaliar(lambda p: responder(p, modelo=MODELO_FORTE), PERGUNTAS[:8])
comparacao = pd.DataFrame({"mini": resumo(base), "forte": resumo(forte)})
comparacao.loc["nota_por_dolar"] = comparacao.loc["nota_media"] / comparacao.loc["custo_total_usd"].replace(0, np.nan)
comparacao'''),

    ("tarefa",
     "**Aumente o conjunto de avaliação.** Poucas perguntas dão pouca confiança. Para 3 itens de `PERGUNTAS`, peça ao "
     "modelo 2 reformulações de cada um (JSON `{\"perguntas\": [...]}`), mantendo a referência e o `doc`. Junte numa "
     "lista `PERGUNTAS_AMPLIADAS` e salve em `../saidas/perguntas_ampliadas.json`. Depois, confira as reformulações à mão.",
     r'''PERGUNTAS_AMPLIADAS = list(PERGUNTAS)
for item in PERGUNTAS[:3]:
    j = perguntar_json(f"Reescreva de 2 jeitos diferentes, como um cliente escreveria: {item['pergunta']}. "
                       'Devolva {"perguntas": ["...", "..."]}', temperature=0.9)
    for nova in j.get("perguntas", [])[:2]:
        PERGUNTAS_AMPLIADAS.append({**item, "pergunta": nova})
with open("../saidas/perguntas_ampliadas.json", "w", encoding="utf-8") as f:
    json.dump(PERGUNTAS_AMPLIADAS, f, ensure_ascii=False, indent=1)
print(len(PERGUNTAS), "->", len(PERGUNTAS_AMPLIADAS))
PERGUNTAS_AMPLIADAS[-4:]'''),
]
