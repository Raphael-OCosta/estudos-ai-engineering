TITULO = "Como medir se a IA acertou"
MISSAO = (
    "Construir a sua **caixa de ferramentas de avaliação**: métricas de linguagem (entropia, perplexidade), métricas "
    "exatas (acerto exato, F1, sobreposição de n-gramas), similaridade por embeddings, **IA como juiz** (e os vieses "
    "dela) e um ranking de modelos por comparação em pares. Sem avaliação, não dá para saber se uma mudança melhorou "
    "ou piorou o produto."
)
ENTREGA = "os módulos `PKG/metricas.py` e `PKG/juiz.py`, que os próximos capítulos usam para medir o assistente."
LEITURA = [("Understanding Language Modeling Metrics", 142), ("Exact Evaluation", 149),
           ("AI as a Judge", 160), ("Ranking Models with Comparative Evaluation", 172)]

PASSOS = [
    ("texto",
     "## Ideia em 30 segundos\n"
     "Avaliar modelos de base é difícil porque as respostas são abertas: há muitas formas certas de dizer a mesma "
     "coisa. Existem três famílias de métodos:\n"
     "- **exatas**: o código confere (testes unitários, acerto exato, sobreposição com uma referência);\n"
     "- **por similaridade**: embeddings dizem se o sentido é parecido;\n"
     "- **subjetivas**: outro modelo dá a nota (IA como juiz). É barato e flexível, mas tem vieses que você precisa "
     "medir."),

    ("tarefa",
     "**Entropia.** Calcule, em bits, a entropia de três distribuições sobre 4 tokens: uniforme "
     "`[0.25]*4`, concentrada `[0.97, 0.01, 0.01, 0.01]` e intermediária `[0.5, 0.3, 0.15, 0.05]`. Quanto maior a "
     "entropia, mais \"em dúvida\" o modelo está.",
     r'''def entropia(p):
    p = np.asarray(p, dtype=float)
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())

for nome, p in [("uniforme", [0.25] * 4), ("concentrada", [0.97, 0.01, 0.01, 0.01]),
                ("intermediária", [0.5, 0.3, 0.15, 0.05])]:
    print(f"{nome:14} {entropia(p):.3f} bits")'''),

    ("tarefa",
     "**Perplexidade a partir dos logprobs.** Perplexidade = `exp(-média dos logprobs)`. Peça duas respostas com "
     "`logprobs=True`: uma factual (\"Quanto é 12 x 12? Responda só o número.\") e uma criativa (\"Invente um nome "
     "para um gato.\"). Calcule a perplexidade de cada uma. Qual o modelo gerou com mais certeza?",
     r'''def perplexidade(resposta):
    lps = [t.logprob for t in resposta.choices[0].logprobs.content]
    return float(np.exp(-np.mean(lps)))

for prompt in ("Quanto é 12 x 12? Responda só o número.", "Invente um nome para um gato."):
    r = conversar([{"role": "user", "content": prompt}], logprobs=True, temperature=1)
    print(f"{perplexidade(r):6.2f}  {prompt}  ->  {r.choices[0].message.content[:40]}")'''),

    ("tarefa",
     "**Correção funcional (o código passa nos testes?).** Peça ao modelo uma função Python `eh_palindromo(texto)` "
     "que ignore espaços, maiúsculas e acentos. Extraia o bloco de código da resposta (regex entre crases), execute "
     "com `exec` num dicionário separado e rode 4 testes. Se não vier código, conte como falha.",
     r'''import unicodedata
resposta = perguntar("Escreva só a função Python eh_palindromo(texto) que ignora espaços, maiúsculas e acentos. "
                     "Devolva apenas o código num bloco ```python.")
bloco = re.search(r"```(?:python)?\n(.*?)```", resposta or "", re.S)
testes = [("Ame a ema", True), ("Socorram-me subi no ônibus em Marrocos", False), ("ovo", True), ("nimbus", False)]
passou = 0
if bloco:
    espaco = {"unicodedata": unicodedata}
    try:
        exec(bloco.group(1), espaco)
        passou = sum(espaco["eh_palindromo"](t) == esperado for t, esperado in testes)
    except Exception as erro:
        print("o código gerado falhou:", erro)
else:
    print("o modelo não devolveu um bloco de código")
print(f"testes que passaram: {passou}/{len(testes)}")'''),

    ("tarefa",
     "**Acerto exato e F1 de tokens.** Escreva `normalizar(t)` (minúsculas, sem acentos, sem pontuação), "
     "`exata(resposta, referencia)` (0 ou 1) e `f1_tokens(resposta, referencia)` (F1 entre os conjuntos de palavras, "
     "como no SQuAD). Teste com a referência \"R$ 29 por usuário por mês.\" e as respostas \"29 reais por usuário "
     "ao mês\" e \"O plano custa R$ 59.\".",
     r'''import string, unicodedata
from collections import Counter

def normalizar(t):
    t = unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode()
    return " ".join(t.translate(str.maketrans("", "", string.punctuation)).split())

def exata(resposta, referencia):
    return int(normalizar(resposta) == normalizar(referencia))

def f1_tokens(resposta, referencia):
    r, g = normalizar(resposta).split(), normalizar(referencia).split()
    comuns = sum((Counter(r) & Counter(g)).values())
    if comuns == 0:
        return 0.0
    precisao, revocacao = comuns / len(r), comuns / len(g)
    return 2 * precisao * revocacao / (precisao + revocacao)

ref = "R$ 29 por usuário por mês."
for resp in ("29 reais por usuário ao mês", "O plano custa R$ 59."):
    print(f"{resp!r:32} exata={exata(resp, ref)} f1={f1_tokens(resp, ref):.2f}")'''),

    ("tarefa",
     "**Sobreposição de n-gramas (a ideia do BLEU/ROUGE).** Escreva `sobreposicao(resposta, referencia, n=2)`: a "
     "fração dos n-gramas da referência que aparecem na resposta. Mostre para n=1 e n=2 com as mesmas frases. "
     "Por que métricas assim penalizam respostas certas escritas de outro jeito?",
     r'''def ngramas(t, n):
    p = normalizar(t).split()
    return [tuple(p[i:i + n]) for i in range(len(p) - n + 1)]

def sobreposicao(resposta, referencia, n=2):
    g = ngramas(referencia, n)
    if not g:
        return 0.0
    r = Counter(ngramas(resposta, n))
    return sum(min(c, r[k]) for k, c in Counter(g).items()) / len(g)

for resp in ("29 reais por usuário ao mês", "O plano custa R$ 59."):
    print(resp, "| n=1:", round(sobreposicao(resp, ref, 1), 2), "| n=2:", round(sobreposicao(resp, ref, 2), 2))'''),

    ("tarefa",
     "**Similaridade semântica.** Com `embeddings` e `similaridade`, compare a referência com: uma paráfrase correta, "
     "uma resposta errada mas parecida e um texto sem relação. A ordem das notas faz sentido?",
     r'''candidatas = ["Cada usuário paga 29 reais mensais.", "Cada usuário paga 59 reais mensais.",
              "O aplicativo funciona sem internet."]
v = embeddings([ref] + candidatas)
for c, s in zip(candidatas, similaridade(v[0], v[1:])[0]):
    print(f"{s:.3f}  {c}")'''),

    ("arquivo",
     "**Módulo de métricas.** Junte num arquivo `metricas.py` as funções `normalizar`, `exata`, `f1_tokens`, "
     "`sobreposicao` e `similaridade_semantica(resposta, referencia)` (cosseno dos embeddings).",
     "metricas.py",
     r'''"""Métricas exatas e por similaridade para avaliar respostas."""
import string
import unicodedata
from collections import Counter

from ia import embeddings, similaridade


def normalizar(t: str) -> str:
    t = unicodedata.normalize("NFKD", (t or "").lower()).encode("ascii", "ignore").decode()
    return " ".join(t.translate(str.maketrans("", "", string.punctuation)).split())


def exata(resposta: str, referencia: str) -> int:
    return int(normalizar(resposta) == normalizar(referencia))


def f1_tokens(resposta: str, referencia: str) -> float:
    r, g = normalizar(resposta).split(), normalizar(referencia).split()
    comuns = sum((Counter(r) & Counter(g)).values())
    if comuns == 0:
        return 0.0
    p, rev = comuns / len(r), comuns / len(g)
    return 2 * p * rev / (p + rev)


def _ngramas(t: str, n: int):
    p = normalizar(t).split()
    return [tuple(p[i:i + n]) for i in range(len(p) - n + 1)]


def sobreposicao(resposta: str, referencia: str, n: int = 2) -> float:
    g = _ngramas(referencia, n)
    if not g:
        return 0.0
    r = Counter(_ngramas(resposta, n))
    return sum(min(c, r[k]) for k, c in Counter(g).items()) / len(g)


def similaridade_semantica(resposta: str, referencia: str) -> float:
    v = embeddings([resposta or " ", referencia])
    return float(similaridade(v[0], v[1])[0, 0])
'''),

    ("tarefa",
     "**IA como juiz.** Escreva um prompt de juiz com uma **rubrica** de 1 a 5 (5 = correta e completa segundo a "
     "referência; 1 = errada ou inventada) que devolve JSON `{\"nota\": int, \"motivo\": str}`. Avalie 3 respostas "
     "para \"Quanto custa o plano Equipe?\": uma certa, uma incompleta e uma errada.",
     r'''RUBRICA = """Você avalia respostas de um assistente de suporte comparando com a resposta de referência.
Nota de 1 a 5: 5 = correta e completa; 4 = correta com pequena omissão; 3 = parcialmente correta;
2 = maioria errada; 1 = errada ou inventada. Devolva JSON: {"nota": inteiro, "motivo": "frase curta"}"""

def julgar(pergunta, resposta, referencia):
    return perguntar_json(f"Pergunta: {pergunta}\nReferência: {referencia}\nResposta avaliada: {resposta}",
                          sistema=RUBRICA, modelo=MODELO_FORTE, temperature=0)

for resp in ("R$ 29 por usuário por mês.", "É pago por usuário.", "Custa R$ 59 por mês."):
    j = julgar("Quanto custa o plano Equipe?", resp, "R$ 29 por usuário por mês.")
    print(j.get("nota"), "|", resp, "|", j.get("motivo"))'''),

    ("tarefa",
     "**Viés de posição.** Juízes tendem a preferir a resposta que aparece primeiro. Peça ao juiz para escolher a "
     "melhor entre A e B (JSON `{\"vencedor\": \"A\"|\"B\"|\"empate\"}`), depois **troque a ordem** e pergunte de novo. "
     "O veredito é consistente?",
     r'''def comparar_uma_vez(pergunta, a, b):
    sistema = ('Compare duas respostas de suporte. Devolva JSON {"vencedor": "A", "B" ou "empate", '
               '"motivo": "frase curta"}.')
    return perguntar_json(f"Pergunta: {pergunta}\nResposta A: {a}\nResposta B: {b}",
                          sistema=sistema, modelo=MODELO_FORTE, temperature=0).get("vencedor")

p = "Posso exportar em JSON no plano grátis?"
boa, ruim = "Não, no plano Grátis só dá para exportar em CSV.", "Sim, qualquer plano exporta JSON."
v1 = comparar_uma_vez(p, boa, ruim)       # boa é A
v2 = comparar_uma_vez(p, ruim, boa)       # boa é B
print("ordem 1:", v1, "| ordem 2:", v2, "| consistente:", (v1, v2) == ("A", "B"))'''),

    ("arquivo",
     "**Módulo do juiz.** Escreva `juiz.py` com `julgar(pergunta, resposta, referencia)` (devolve `nota` e `motivo`) "
     "e `comparar(pergunta, a, b)`, que pergunta nas duas ordens e só declara vencedor se as duas concordarem; "
     "senão devolve `empate`.",
     "juiz.py",
     r'''"""IA como juiz: nota com rubrica e comparação em pares com controle de viés de posição."""
from ia import MODELO_FORTE, perguntar_json

RUBRICA = """Você avalia respostas de um assistente de suporte comparando com a resposta de referência.
Nota de 1 a 5: 5 = correta e completa; 4 = correta com pequena omissão; 3 = parcialmente correta;
2 = maioria errada; 1 = errada ou inventada. Devolva JSON: {"nota": inteiro, "motivo": "frase curta"}"""

COMPARA = ('Compare duas respostas de suporte para a mesma pergunta. Devolva JSON '
           '{"vencedor": "A", "B" ou "empate", "motivo": "frase curta"}.')


def julgar(pergunta: str, resposta: str, referencia: str, modelo: str = MODELO_FORTE) -> dict:
    j = perguntar_json(f"Pergunta: {pergunta}\nReferência: {referencia}\nResposta avaliada: {resposta}",
                       sistema=RUBRICA, modelo=modelo, temperature=0)
    nota = j.get("nota", j.get("pontuacao", 0))
    return {"nota": int(nota) if str(nota).isdigit() else 0, "motivo": j.get("motivo", "")}


def _uma_vez(pergunta, a, b, modelo):
    return perguntar_json(f"Pergunta: {pergunta}\nResposta A: {a}\nResposta B: {b}",
                          sistema=COMPARA, modelo=modelo, temperature=0).get("vencedor", "empate")


def comparar(pergunta: str, a: str, b: str, modelo: str = MODELO_FORTE) -> str:
    v1 = _uma_vez(pergunta, a, b, modelo)
    v2 = _uma_vez(pergunta, b, a, modelo)
    if v1 == "A" and v2 == "B":
        return "A"
    if v1 == "B" and v2 == "A":
        return "B"
    return "empate"
'''),

    ("tarefa",
     "**Ranking por comparação (Elo).** Quatro modelos fictícios disputaram partidas em pares (os resultados estão "
     "abaixo, já prontos). Implemente a atualização Elo (`esperado = 1 / (1 + 10**((rb - ra) / 400))`, "
     "`ra += K * (resultado - esperado)`, K=32), comece todos em 1.000, percorra as partidas 3 vezes e mostre o "
     "ranking.",
     r'''partidas = [("alfa", "beta", 1), ("alfa", "gama", 1), ("alfa", "delta", 0.5), ("beta", "gama", 1),
            ("beta", "delta", 0), ("gama", "delta", 0), ("alfa", "beta", 1), ("delta", "beta", 1),
            ("gama", "alfa", 0), ("delta", "alfa", 0.5), ("gama", "beta", 0), ("delta", "gama", 1)]
elo = {m: 1000.0 for m in ("alfa", "beta", "gama", "delta")}
K = 32
for _ in range(3):
    for a, b, resultado in partidas:          # resultado: 1 = a venceu, 0 = b venceu, 0.5 = empate
        esperado = 1 / (1 + 10 ** ((elo[b] - elo[a]) / 400))
        elo[a] += K * (resultado - esperado)
        elo[b] += K * ((1 - resultado) - (1 - esperado))
pd.Series(elo).sort_values(ascending=False).round(0)'''),

    ("tarefa",
     "**Use os módulos.** Importe `f1_tokens` e `similaridade_semantica` de `PKG.metricas` e `julgar` de "
     "`PKG.juiz`. Avalie a resposta do seu `nucleo.responder` para \"Qual o horário do suporte?\" com as três "
     "medidas, contra a referência de `PERGUNTAS`.",
     r'''from PKG.metricas import f1_tokens, similaridade_semantica
from PKG.juiz import julgar
from PKG.nucleo import responder
item = next(p for p in PERGUNTAS if p["pergunta"] == "Qual o horário do suporte?")
resp = responder(item["pergunta"])["texto"]
print(resp)
print("f1:", round(f1_tokens(resp, item["referencia"]), 2),
      "| semântica:", round(similaridade_semantica(resp, item["referencia"]), 2),
      "| juiz:", julgar(item["pergunta"], resp, item["referencia"]))'''),
]
