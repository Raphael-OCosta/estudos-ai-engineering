TITULO = "Por dentro do modelo: tokens, amostragem e saídas estruturadas"
MISSAO = (
    "Entender, mexendo nos números, as três coisas que mais afetam o seu produto: **tokens** (custo e limite de "
    "contexto), **amostragem** (por que o modelo responde diferente a cada vez) e **saídas estruturadas** (como fazer o "
    "modelo devolver dados que o seu código consegue usar)."
)
ENTREGA = "o módulo `PKG/estruturado.py`, que transforma um chamado de cliente em um objeto validado (categoria, prioridade, resumo)."
LEITURA = [("Training Data: Multilingual Models", 75), ("Sampling Fundamentals e Sampling Strategies", 112),
           ("Test Time Compute", 120), ("Structured Outputs", 123), ("The Probabilistic Nature of AI", 129)]

PASSOS = [
    ("texto",
     "## Ideia em 30 segundos\n"
     "O modelo não lê palavras: lê **tokens**, pedaços de texto. A cada passo ele calcula uma pontuação (*logit*) para "
     "cada token possível, transforma em probabilidades (*softmax*) e **sorteia** o próximo. A temperatura, o top-k e "
     "o top-p mudam esse sorteio. Por isso a mesma pergunta pode ter respostas diferentes, e é por isso também que "
     "vale a pena forçar um formato (JSON) quando o resultado vai para um programa."),

    ("tarefa",
     "**Tokens na prática.** Com `tiktoken` (`tiktoken.get_encoding(\"o200k_base\")`), codifique a frase "
     "\"A Nimbus organiza as tarefas da sua equipe.\". Mostre o número de tokens e cada pedaço decodificado "
     "(`enc.decode([t])`).",
     r'''import tiktoken
enc = tiktoken.get_encoding("o200k_base")
ids = enc.encode("A Nimbus organiza as tarefas da sua equipe.")
print(len(ids), "tokens")
print([enc.decode([t]) for t in ids])'''),

    ("tarefa",
     "**Português custa mais?** Compare o número de tokens de 3 frases em português e das mesmas frases em inglês "
     "(use `contar_tokens`). Mostre a razão PT/EN de cada uma e a média.",
     r'''pares = [
    ("Esqueci minha senha e não consigo entrar.", "I forgot my password and can't log in."),
    ("Quero cancelar a assinatura no fim do mês.", "I want to cancel the subscription at the end of the month."),
    ("O aplicativo fecha sozinho quando abro um anexo.", "The app closes by itself when I open an attachment."),
]
razoes = [contar_tokens(pt) / contar_tokens(en) for pt, en in pares]
for (pt, en), r in zip(pares, razoes):
    print(f"{contar_tokens(pt):3} x {contar_tokens(en):3}  razão {r:.2f}")
print("média:", round(float(np.mean(razoes)), 2))'''),

    ("tarefa",
     "**Temperatura à mão.** Com os logits `[2.0, 1.0, 0.5, 0.1]` para os tokens `[\"sim\", \"não\", \"talvez\", "
     "\"nunca\"]`, calcule o softmax com temperatura (`logits / T`) para `T = 0.2, 1 e 2`. Mostre numa tabela. O que "
     "acontece com o token mais provável quando T cai?",
     r'''logits = np.array([2.0, 1.0, 0.5, 0.1])
tokens = ["sim", "não", "talvez", "nunca"]

def softmax(z, T=1.0):
    z = z / T
    e = np.exp(z - z.max())
    return e / e.sum()

pd.DataFrame({f"T={T}": softmax(logits, T) for T in (0.2, 1, 2)}, index=tokens).round(3)'''),

    ("tarefa",
     "**Top-k e top-p.** Escreva `amostrar(logits, T=1.0, top_k=None, top_p=None, rng=None)` que: aplica a "
     "temperatura; se houver `top_k`, mantém só os k maiores; se houver `top_p`, mantém os mais prováveis até somar "
     "p; renormaliza e sorteia um índice. Sorteie 2.000 vezes com `top_k=2` e com `top_p=0.8` e conte quantas vezes "
     "saiu cada token.",
     r'''from collections import Counter

def amostrar(logits, T=1.0, top_k=None, top_p=None, rng=None):
    rng = rng or np.random.default_rng()
    p = softmax(np.asarray(logits, dtype=float), T)
    ordem = np.argsort(p)[::-1]
    manter = np.ones_like(p, dtype=bool)
    if top_k is not None:
        manter[:] = False
        manter[ordem[:top_k]] = True
    if top_p is not None:
        acumulada = np.cumsum(p[ordem])
        corte = np.searchsorted(acumulada, top_p) + 1
        mascara = np.zeros_like(manter)
        mascara[ordem[:corte]] = True
        manter &= mascara
    p = np.where(manter, p, 0)
    return rng.choice(len(p), p=p / p.sum())

rng = np.random.default_rng(0)
for nome, kw in [("top_k=2", {"top_k": 2}), ("top_p=0.8", {"top_p": 0.8})]:
    c = Counter(tokens[amostrar(logits, rng=rng, **kw)] for _ in range(2000))
    print(nome, dict(c))'''),

    ("tarefa",
     "**Logprobs de verdade.** Peça ao modelo para completar \"A capital da Austrália é\" com `logprobs=True` e "
     "`top_logprobs=3`, `max_tokens=5`. Para cada token gerado, mostre a probabilidade (`np.exp(logprob)`) e as "
     "alternativas que o modelo considerou.",
     r'''r = conversar([{"role": "user", "content": "Complete com uma palavra: A capital da Austrália é"}],
              logprobs=True, top_logprobs=3, max_tokens=5)
for t in r.choices[0].logprobs.content:
    alternativas = ", ".join(f"{a.token!r}:{np.exp(a.logprob):.2f}" for a in t.top_logprobs)
    print(f"{t.token!r:15} p={np.exp(t.logprob):.3f} | {alternativas}")'''),

    ("tarefa",
     "**Temperatura no modelo.** Peça 3 amostras (`n=3`) de um slogan para a Nimbus com `temperature=0` e depois com "
     "`temperature=1.2`. Quantas respostas **diferentes** saíram em cada caso?",
     r'''for T in (0, 1.2):
    r = conversar([{"role": "user", "content": "Crie um slogan curto para a Nimbus, app de tarefas para equipes."}],
                  n=3, temperature=T)
    textos = [c.message.content for c in r.choices]
    print(f"T={T}: {len(set(textos))} diferentes")
    for t in textos:
        print("   ", t[:90])'''),

    ("tarefa",
     "**Gastar mais tempo de teste para acertar mais (autoconsistência).** Faça a pergunta "
     "\"Uma equipe de 7 pessoas no plano Equipe paga quanto por mês, a R$ 29 por pessoa? Responda só com o número.\" "
     "com `n=5` e `temperature=0.8`. Extraia o número de cada resposta com regex e escolha o mais votado "
     "(`Counter`). Se nenhum número aparecer, mostre `None`.",
     r'''from collections import Counter
r = conversar([{"role": "user", "content": "Uma equipe de 7 pessoas no plano Equipe paga quanto por mês, "
                "a R$ 29 por pessoa? Responda só com o número."}], n=5, temperature=0.8)
numeros = []
for c in r.choices:
    achado = re.findall(r"\d+[.,]?\d*", c.message.content or "")
    if achado:
        numeros.append(achado[-1].replace(",", "."))
votos = Counter(numeros)
print(votos, "-> escolhido:", votos.most_common(1)[0][0] if votos else None)'''),

    ("tarefa",
     "**JSON com esquema.** Peça a classificação do chamado \"Fui cobrado duas vezes este mês\" usando "
     "`response_format` do tipo `json_schema`, com os campos `categoria` (um de `CATEGORIAS`), `prioridade` "
     "(`baixa`, `media`, `alta`) e `resumo`. Use `\"strict\": True`, `additionalProperties: False` e todos os campos "
     "em `required`. Converta com `json.loads`.",
     r'''esquema = {
    "name": "chamado",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "categoria": {"type": "string", "enum": CATEGORIAS},
            "prioridade": {"type": "string", "enum": ["baixa", "media", "alta"]},
            "resumo": {"type": "string"},
        },
        "required": ["categoria", "prioridade", "resumo"],
        "additionalProperties": False,
    },
}
r = conversar([{"role": "user", "content": "Classifique o chamado: Fui cobrado duas vezes este mês"}],
              response_format={"type": "json_schema", "json_schema": esquema})
dados = json.loads(r.choices[0].message.content)
dados'''),

    ("arquivo",
     "**Módulo de saída estruturada.** Escreva `estruturado.py` com:\n"
     "- a classe `Chamado` (pydantic) com `categoria: Literal[...]`, `prioridade: Literal[\"baixa\", \"media\", "
     "\"alta\"]` e `resumo: str`;\n"
     "- `classificar_chamado(texto)`: pede o JSON com o esquema gerado por `Chamado.model_json_schema()` (ajuste "
     "`additionalProperties`), valida com `Chamado.model_validate_json` e, se a validação falhar, tenta mais uma vez "
     "antes de desistir.",
     "estruturado.py",
     r'''"""Transforma o texto de um chamado em dados validados."""
from typing import Literal

from pydantic import BaseModel, ValidationError

from ia import conversar

SISTEMA = ("Você classifica chamados de clientes da Nimbus. Categorias: cobranca (pagamento, fatura), "
           "acesso (login, senha, convite), bug (algo quebrado), duvida (como usar), cancelamento (encerrar conta).")


class Chamado(BaseModel):
    categoria: Literal["cobranca", "acesso", "bug", "duvida", "cancelamento"]
    prioridade: Literal["baixa", "media", "alta"]
    resumo: str


def _esquema() -> dict:
    s = Chamado.model_json_schema()
    s["additionalProperties"] = False
    s["required"] = list(s["properties"])
    return {"name": "chamado", "strict": True, "schema": s}


def classificar_chamado(texto: str, tentativas: int = 2) -> Chamado:
    erro = None
    for _ in range(tentativas):
        r = conversar([{"role": "system", "content": SISTEMA}, {"role": "user", "content": texto}],
                      response_format={"type": "json_schema", "json_schema": _esquema()}, temperature=0)
        try:
            return Chamado.model_validate_json(r.choices[0].message.content)
        except ValidationError as e:
            erro = e
    raise ValueError(f"o modelo não devolveu um chamado válido: {erro}")
'''),

    ("tarefa",
     "**Mede o classificador.** Rode `classificar_chamado` em todos os `TICKETS`, monte um `DataFrame` com o texto, "
     "a categoria certa e a prevista, e mostre a acurácia.",
     r'''from PKG.estruturado import classificar_chamado
linhas = []
for texto, certa in TICKETS:
    c = classificar_chamado(texto)
    linhas.append({"texto": texto[:50], "certa": certa, "prevista": c.categoria, "prioridade": c.prioridade})
df = pd.DataFrame(linhas)
print("acurácia:", round((df.certa == df.prevista).mean(), 2))
df'''),

    ("tarefa",
     "**O modelo é probabilístico.** Faça 5 vezes a mesma pergunta factual (\"Em que ano foi lançado o primeiro "
     "iPhone? Responda só o ano.\") com `temperature=1`, e depois 5 vezes com `temperature=0` e `seed=42`. Conte as "
     "respostas distintas. Qual configuração você usaria num produto?",
     r'''for opcoes in ({"temperature": 1}, {"temperature": 0, "seed": 42}):
    respostas = [perguntar("Em que ano foi lançado o primeiro iPhone? Responda só o ano.", **opcoes) for _ in range(5)]
    print(opcoes, "->", len(set(respostas)), "distintas:", set(respostas))'''),
]
