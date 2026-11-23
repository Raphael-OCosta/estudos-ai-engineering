TITULO = "Engenharia de dados para IA"
MISSAO = (
    "Montar um **pipeline de dados de treino e de avaliação** de qualidade, partindo de dados sujos. Ele vai:\n"
    "1. inspecionar;\n"
    "2. tirar duplicatas exatas e quase iguais (com MinHash feito à mão);\n"
    "3. limpar e filtrar (inclusive dados pessoais);\n"
    "4. medir a cobertura;\n"
    "5. **gerar dados sintéticos** com o modelo onde faltam e verificar esses dados com um juiz;\n"
    "6. formatar para treino.\n\n"
    "Dados bons valem mais que um modelo maior."
)
ENTREGA = "o módulo `PKG/dados_treino.py` (pipeline limpar → deduplicar → filtrar → formatar) e um conjunto final com relatório de cada etapa."
LEITURA = [("Data Curation: Quality, Coverage, Quantity", 389), ("AI-Powered Data Synthesis", 410),
           ("Model Distillation", 419), ("Data Processing: Inspect, Deduplicate, Clean, Format", 420)]

PASSOS = [
    ("texto",
     "## Ideia em 30 segundos\n"
     "Três perguntas guiam a curadoria:\n"
     "- **qualidade**: os exemplos estão certos?\n"
     "- **cobertura**: eles cobrem os casos reais?\n"
     "- **quantidade**: são suficientes?\n\n"
     "Dados sintéticos (gerados por um modelo) tapam buracos de cobertura, mas precisam de verificação, porque o "
     "modelo também erra e repete padrões."),

    ("pronto",
     "Dados sujos de propósito (já vem pronto): pares pergunta/resposta com duplicatas, quase duplicatas, vazios, "
     "inglês, textos longos demais e dados pessoais.",
     r'''sujos = [{"pergunta": p["pergunta"], "resposta": p["referencia"], "doc": p["doc"]} for p in PERGUNTAS]
sujos += [
    {"pergunta": "Quanto custa o plano Equipe?", "resposta": "R$ 29 por usuário por mês.", "doc": "planos"},
    {"pergunta": "quanto custa o plano equipe??", "resposta": "R$ 29 por usuário por mês.", "doc": "planos"},
    {"pergunta": "Quanto custa o plano Equipe por mês?", "resposta": "R$ 29 por usuário/mês.", "doc": "planos"},
    {"pergunta": "", "resposta": "Sem pergunta.", "doc": "planos"},
    {"pergunta": "How do I reset my password?", "resposta": "Click on forgot password.", "doc": "senha"},
    {"pergunta": "Meu e-mail é joana.silva@gmail.com e meu CPF 123.456.789-00, não consigo entrar.",
     "resposta": "Use Esqueci minha senha.", "doc": "senha"},
    {"pergunta": "Explique tudo sobre a Nimbus " + "por favor " * 80, "resposta": "...", "doc": "planos"},
]
df = pd.DataFrame(sujos)
print(len(df), "linhas")'''),

    ("tarefa",
     "**Inspeção.** Mostre: número de linhas, quantas perguntas vazias, a distribuição do tamanho das perguntas em "
     "palavras (`describe`) e as 3 maiores. Inspecionar antes de tudo evita surpresas.",
     r'''df["palavras"] = df.pergunta.str.split().str.len()
print("vazias:", (df.pergunta.str.strip() == "").sum())
display(df.palavras.describe())
df.nlargest(3, "palavras")[["pergunta", "palavras"]]'''),

    ("tarefa",
     "**Duplicatas exatas.** Normalize as perguntas (minúsculas, sem acento, sem pontuação, espaços únicos), calcule "
     "um hash (`hashlib.md5`) e remova as repetidas. Quantas saíram?",
     r'''import hashlib, string, unicodedata

def normalizar(t):
    t = unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode()
    return " ".join(t.translate(str.maketrans("", "", string.punctuation)).split())

df["hash"] = df.pergunta.map(lambda t: hashlib.md5(normalizar(t).encode()).hexdigest())
sem_exatas = df.drop_duplicates("hash")
print(len(df), "->", len(sem_exatas))'''),

    ("tarefa",
     "**Quase duplicatas com MinHash.** Implemente:\n"
     "1. `shingles(t, k=3)`: o conjunto de trincas de palavras do texto normalizado;\n"
     "2. a Jaccard exata;\n"
     "3. um MinHash com 64 funções de hash (`hash((semente, s))`): a assinatura é o mínimo de cada função, e a "
     "estimativa da Jaccard é a fração de posições iguais.\n\n"
     "Compare a Jaccard exata com a estimada para dois pares de perguntas e marque como quase duplicatas os pares "
     "com estimativa >= 0,5.",
     r'''def shingles(t, k=3):
    p = normalizar(t).split()
    return {" ".join(p[i:i + k]) for i in range(max(1, len(p) - k + 1))}

def jaccard(a, b):
    return len(a & b) / len(a | b) if a | b else 0.0

def minhash(conjunto, n=64):
    return np.array([min(hash((semente, s)) for s in conjunto) for semente in range(n)])

perguntas = sem_exatas.pergunta.tolist()
assinaturas = [minhash(shingles(p)) for p in perguntas]
pares = []
for i in range(len(perguntas)):
    for j in range(i + 1, len(perguntas)):
        estimada = float((assinaturas[i] == assinaturas[j]).mean())
        if estimada >= 0.5:
            pares.append((perguntas[i], perguntas[j], round(estimada, 2),
                          round(jaccard(shingles(perguntas[i]), shingles(perguntas[j])), 2)))
pd.DataFrame(pares, columns=["a", "b", "minhash", "jaccard exata"])'''),

    ("tarefa",
     "**Limpeza e filtros.** Escreva regras e aplique em `sem_exatas`:\n"
     "- tirar perguntas vazias ou com mais de 60 palavras;\n"
     "- tirar as que parecem inglês (heurística: palavras como `the`, `how`, `my`, `do`);\n"
     "- **mascarar** e-mails e CPFs com regex, trocando por `[EMAIL]` e `[CPF]`.\n\n"
     "Mostre quantas linhas sobraram e a pergunta mascarada.",
     r'''INGLES = {"the", "how", "my", "do", "i", "is", "what"}
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")

def parece_ingles(t):
    palavras = set(normalizar(t).split())
    return len(palavras & INGLES) >= 2

def mascarar(t):
    return CPF.sub("[CPF]", EMAIL.sub("[EMAIL]", t))

limpo = sem_exatas[(sem_exatas.pergunta.str.strip() != "") & (sem_exatas.palavras <= 60)]
limpo = limpo[~limpo.pergunta.map(parece_ingles)].copy()
limpo["pergunta"] = limpo.pergunta.map(mascarar)
print(len(sem_exatas), "->", len(limpo))
limpo[limpo.pergunta.str.contains(r"\[EMAIL\]|\[CPF\]")].pergunta.tolist()'''),

    ("tarefa",
     "**Cobertura.** Conte quantas perguntas há por documento (`doc`) e liste os documentos da Nimbus com **1 pergunta "
     "ou menos**. São esses os buracos que os dados sintéticos vão tapar.",
     r'''contagem = limpo.doc.value_counts()
poucas = [d["id"] for d in DOCUMENTOS if contagem.get(d["id"], 0) <= 1]
display(contagem.to_frame("perguntas"))
print("documentos com 1 pergunta ou menos:", poucas)'''),

    ("tarefa",
     "**Aumento tradicional (sem IA).** Gere variações de cada pergunta trocando palavras por sinônimos de um "
     "dicionário pequeno (por exemplo, `quanto custa` → `qual o preço de`, `consigo` → `é possível`). Quantas "
     "perguntas novas saíram?",
     r'''SINONIMOS = {"quanto custa": "qual o preço de", "consigo": "é possível", "posso": "é possível",
             "tem": "existe", "como": "de que jeito"}

def variacoes(t):
    saida = []
    for a, b in SINONIMOS.items():
        if a in t.lower():
            saida.append(re.sub(a, b, t, flags=re.I))
    return saida

novas = [(v, row.resposta, row.doc) for row in limpo.itertuples() for v in variacoes(row.pergunta)]
print(len(novas), "variações; exemplos:", [n[0] for n in novas[:3]])'''),

    ("tarefa",
     "**Dados sintéticos com IA.** Para cada documento com poucas perguntas, peça ao modelo 2 pares pergunta/resposta "
     "baseados **só** no texto do documento (JSON `{\"itens\": [{\"pergunta\": ..., \"resposta\": ...}]}`). Guarde em "
     "`sinteticos` com o `doc` de origem.",
     r'''sinteticos = []
for doc_id in poucas:
    doc = next(d for d in DOCUMENTOS if d["id"] == doc_id)
    j = perguntar_json("Crie 2 perguntas que um cliente faria e as respostas, usando SOMENTE este texto. "
                       'Devolva {"itens": [{"pergunta": "...", "resposta": "..."}]}\n\n' + doc["texto"],
                       temperature=0.7)
    for item in j.get("itens", [])[:2]:
        if isinstance(item, dict) and item.get("pergunta"):
            sinteticos.append({"pergunta": item["pergunta"], "resposta": item.get("resposta", ""), "doc": doc_id})
print(len(sinteticos), "pares sintéticos")
pd.DataFrame(sinteticos)'''),

    ("tarefa",
     "**Verificação com juiz.** Para cada par sintético, pergunte ao `MODELO_FORTE` se a resposta está correta e é "
     "sustentada pelo documento (JSON `{\"relevante\": true/false, \"motivo\": ...}`). Mantenha só os aprovados. "
     "Quantos passaram?",
     r'''aprovados = []
for s in sinteticos:
    doc = next(d["texto"] for d in DOCUMENTOS if d["id"] == s["doc"])
    v = perguntar_json(f"Documento: {doc}\nPergunta: {s['pergunta']}\nResposta: {s['resposta']}\n"
                       'A resposta está correta e sustentada pelo documento? Devolva {"relevante": true ou false, '
                       '"motivo": "..."}', modelo=MODELO_FORTE, temperature=0)
    if v.get("relevante") is True:
        aprovados.append(s)
print(f"{len(aprovados)}/{len(sinteticos)} aprovados")'''),

    ("arquivo",
     "**Módulo do pipeline.** Escreva `dados_treino.py` com `preparar_conjunto(pares, sistema)`, que recebe uma lista "
     "de dicts (`pergunta`, `resposta`) e faz, contando o que sai em cada etapa:\n"
     "1. tira vazios;\n"
     "2. tira duplicatas exatas;\n"
     "3. tira perguntas com mais de 60 palavras;\n"
     "4. mascara e-mail e CPF;\n"
     "5. formata no padrão de conversa (`messages`).\n\n"
     "Devolve `(exemplos, relatorio)`, em que `relatorio` é um dict etapa → quantidade.",
     "dados_treino.py",
     r'''"""Pipeline de preparação de dados de treino: limpar -> deduplicar -> filtrar -> formatar."""
import hashlib
import re
import string
import unicodedata

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")


def _normalizar(t: str) -> str:
    t = unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode()
    return " ".join(t.translate(str.maketrans("", "", string.punctuation)).split())


def _mascarar(t: str) -> str:
    return CPF.sub("[CPF]", EMAIL.sub("[EMAIL]", t))


def preparar_conjunto(pares: list[dict], sistema: str, max_palavras: int = 60):
    relatorio = {"entrada": len(pares)}
    pares = [p for p in pares if p.get("pergunta", "").strip() and p.get("resposta", "").strip()]
    relatorio["sem vazios"] = len(pares)
    vistos, unicos = set(), []
    for p in pares:
        h = hashlib.md5(_normalizar(p["pergunta"]).encode()).hexdigest()
        if h not in vistos:
            vistos.add(h)
            unicos.append(p)
    relatorio["sem duplicatas"] = len(unicos)
    curtos = [p for p in unicos if len(p["pergunta"].split()) <= max_palavras]
    relatorio["tamanho ok"] = len(curtos)
    exemplos = [{"messages": [{"role": "system", "content": sistema},
                              {"role": "user", "content": _mascarar(p["pergunta"])},
                              {"role": "assistant", "content": _mascarar(p["resposta"])}]} for p in curtos]
    relatorio["formatados"] = len(exemplos)
    return exemplos, relatorio
'''),

    ("tarefa",
     "**Rode o pipeline completo.** Junte os dados sujos, as variações por sinônimo e os sintéticos aprovados, passe "
     "por `preparar_conjunto` e grave `../saidas/conjunto_final.jsonl`. Mostre o relatório como tabela.",
     r'''from PKG.dados_treino import preparar_conjunto
todos = sujos + [{"pergunta": p, "resposta": r, "doc": d} for p, r, d in novas] + aprovados
exemplos, relatorio = preparar_conjunto(todos, sistema="Você é o suporte da Nimbus. Responda em até 3 frases.")
with open("../saidas/conjunto_final.jsonl", "w", encoding="utf-8") as f:
    for e in exemplos:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")
pd.Series(relatorio, name="linhas").to_frame()'''),

    ("tarefa",
     "**Destilação.** Ideia: o modelo forte gera as respostas e um modelo menor aprende com elas. Para 3 perguntas "
     "dos `TICKETS`, gere a resposta de suporte com `MODELO_FORTE` (\"professor\") e monte os exemplos de treino do "
     "\"aluno\" no formato `messages`. Quanto isso custou (`gasto()`)?",
     r'''professor = []
for texto, _ in TICKETS[:3]:
    resposta = perguntar(texto, sistema="Você é o suporte da Nimbus. Responda em até 3 frases.", modelo=MODELO_FORTE)
    professor.append({"messages": [{"role": "user", "content": texto}, {"role": "assistant", "content": resposta}]})
print(json.dumps(professor[0], ensure_ascii=False, indent=1)[:400])
print(gasto())'''),
]
