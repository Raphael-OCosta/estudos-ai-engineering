TITULO = "Otimização de inferência: rápido e barato"
MISSAO = (
    "Medir e cortar **latência e custo** do assistente. Você vai medir as métricas que o usuário sente (tempo até o "
    "primeiro token, tempo por token), ver percentis, ganhar vazão com chamadas em paralelo e criar **cache exato e "
    "semântico**. Também vai fazer as contas que explicam o hardware: memória do KV cache, limite por memória × por "
    "cálculo e decodificação especulativa."
)
ENTREGA = "o módulo `PKG/cache.py` (cache exato + semântico), que o assistente final usa para responder perguntas repetidas sem chamar o modelo."
LEITURA = [("Inference Overview", 430), ("Inference Performance Metrics", 436), ("Model Optimization", 450),
           ("Inference Service Optimization", 464)]

PASSOS = [
    ("texto",
     "## Ideia em 30 segundos\n"
     "Gerar texto tem duas fases:\n"
     "- **prefill**: ler o prompt inteiro; é limitado pelo cálculo e define o tempo até o primeiro token, o "
     "**TTFT**;\n"
     "- **decode**: gerar token por token; é limitado pela memória e define o tempo por token, o **TPOT**.\n\n"
     "Para o usuário, *streaming* faz a resposta parecer mais rápida. Para o caixa, o que conta é a **vazão** "
     "(requisições por segundo) e o que você deixa de chamar (cache)."),

    ("tarefa",
     "**TTFT e TPOT com streaming.** Com `conversar(..., stream=True)`, peça uma explicação de 3 frases. Marque o "
     "tempo do primeiro pedaço de texto (TTFT) e o total. Calcule o TPOT aproximado = (total - TTFT) / (número de "
     "pedaços - 1).",
     r'''t0 = time.perf_counter()
ttft, pedacos, texto = None, 0, ""
for evento in conversar([{"role": "user", "content": "Explique em 3 frases o que é cache."}], stream=True):
    if evento.choices and evento.choices[0].delta.content:
        if ttft is None:
            ttft = time.perf_counter() - t0
        pedacos += 1
        texto += evento.choices[0].delta.content
total = time.perf_counter() - t0
print(f"TTFT {ttft:.3f}s | total {total:.3f}s | TPOT ~{(total - ttft) / max(1, pedacos - 1) * 1000:.1f} ms")
print(texto)'''),

    ("tarefa",
     "**Percentis.** A média esconde os piores casos. Faça 8 chamadas curtas, guarde as latências e mostre p50, p90 "
     "e o máximo.",
     r'''lat = []
for i in range(8):
    t0 = time.perf_counter()
    perguntar(f"Diga um número de 1 a 10. ({i})", max_tokens=5)
    lat.append(time.perf_counter() - t0)
print(f"p50 {np.percentile(lat, 50):.2f}s | p90 {np.percentile(lat, 90):.2f}s | máx {max(lat):.2f}s")'''),

    ("tarefa",
     "**Vazão com concorrência.** Responda 8 perguntas de `PERGUNTAS`: primeiro em sequência, depois com "
     "`ThreadPoolExecutor(max_workers=4)`. Compare o tempo total e as requisições por segundo. (Chamadas de API "
     "passam a maior parte do tempo esperando a rede, por isso threads ajudam.)",
     r'''from concurrent.futures import ThreadPoolExecutor
qs = [p["pergunta"] for p in PERGUNTAS[:8]]
t0 = time.perf_counter(); [perguntar(q, max_tokens=60) for q in qs]; seq = time.perf_counter() - t0
t0 = time.perf_counter()
with ThreadPoolExecutor(max_workers=4) as ex:
    list(ex.map(lambda q: perguntar(q, max_tokens=60), qs))
par = time.perf_counter() - t0
print(f"sequencial {seq:.2f}s ({len(qs) / seq:.1f} req/s) | paralelo {par:.2f}s ({len(qs) / par:.1f} req/s)")'''),

    ("tarefa",
     "**Limite a saída.** Tokens de saída custam mais e demoram mais (são gerados um a um). Compare a mesma pergunta "
     "com `max_tokens=300` e com `max_tokens=40` mais a instrução \"responda em uma frase\": latência e tokens de "
     "saída.",
     r'''for opcoes, sufixo in (({"max_tokens": 300}, ""), ({"max_tokens": 40}, " Responda em uma frase.")):
    t0 = time.perf_counter()
    r = conversar([{"role": "user", "content": "Como funciona o cancelamento de uma assinatura de software?" + sufixo}],
                  **opcoes)
    print(f"{opcoes} -> {time.perf_counter() - t0:.2f}s, {r.usage.completion_tokens} tokens de saída")'''),

    ("tarefa",
     "**Cache exato.** Escreva `perguntar_com_cache(prompt)`, que guarda a resposta num dict com a chave "
     "`sha256(modelo + prompt)`. Chame duas vezes a mesma pergunta e mostre o tempo de cada chamada.",
     r'''import hashlib
CACHE = {}

def perguntar_com_cache(prompt, modelo=MODELO):
    chave = hashlib.sha256((modelo + "|" + prompt).encode()).hexdigest()
    if chave not in CACHE:
        CACHE[chave] = perguntar(prompt, modelo=modelo, temperature=0)
    return CACHE[chave]

for tentativa in (1, 2):
    t0 = time.perf_counter()
    perguntar_com_cache("Qual o horário do suporte da Nimbus?")
    print(f"chamada {tentativa}: {(time.perf_counter() - t0) * 1000:.1f} ms")'''),

    ("tarefa",
     "**Cache semântico.** Perguntas iguais escritas de jeitos diferentes deveriam reaproveitar a resposta. Guarde "
     "(vetor, resposta) numa lista. Numa pergunta nova, se a maior similaridade com as guardadas passar de um "
     "**limiar**, devolva a guardada. Teste com 3 paráfrases de \"Quanto custa o plano Equipe?\" e uma pergunta "
     "diferente, com limiar 0,85. Que risco um limiar baixo demais traz?",
     r'''guardados = []
def cache_semantico(pergunta, limiar=0.85):
    v = embeddings(pergunta)[0]
    if guardados:
        sims = similaridade(v, np.array([g[0] for g in guardados]))[0]
        i = int(np.argmax(sims))
        if sims[i] >= limiar:
            return guardados[i][1], round(float(sims[i]), 3), True
    resposta = perguntar(pergunta, temperature=0)
    guardados.append((v, resposta))
    return resposta, None, False

for q in ("Quanto custa o plano Equipe?", "qual o preço do plano equipe", "Quanto custa o plano Equipe por mês?",
          "Quanto custa o plano Empresa?"):
    _, sim, acerto = cache_semantico(q)
    print(f"cache={acerto!s:5} sim={sim} | {q}")
# limiar baixo: "plano Equipe" e "plano Empresa" podem parecer iguais e o cliente recebe o preço errado'''),

    ("arquivo",
     "**Módulo de cache.** Escreva `cache.py` com a classe `CacheRespostas(limiar=0.9)`:\n"
     "- `buscar(pergunta)` primeiro tenta o cache **exato** (texto normalizado) e depois o **semântico**; devolve "
     "`(resposta, tipo)` ou `(None, None)`;\n"
     "- `guardar(pergunta, resposta)`;\n"
     "- `estatisticas()`, com acertos exatos, semânticos e faltas.",
     "cache.py",
     r'''"""Cache de respostas: exato (texto normalizado) e semântico (embeddings)."""
import numpy as np

from ia import embeddings, similaridade


def _norm(t: str) -> str:
    return " ".join(t.lower().split())


class CacheRespostas:
    def __init__(self, limiar: float = 0.9):
        self.limiar = limiar
        self.exato = {}
        self.vetores, self.respostas = [], []
        self.stats = {"exato": 0, "semantico": 0, "falta": 0}

    def buscar(self, pergunta: str):
        chave = _norm(pergunta)
        if chave in self.exato:
            self.stats["exato"] += 1
            return self.exato[chave], "exato"
        if self.vetores:
            sims = similaridade(embeddings(pergunta)[0], np.array(self.vetores))[0]
            i = int(np.argmax(sims))
            if sims[i] >= self.limiar:
                self.stats["semantico"] += 1
                return self.respostas[i], "semantico"
        self.stats["falta"] += 1
        return None, None

    def guardar(self, pergunta: str, resposta) -> None:
        self.exato[_norm(pergunta)] = resposta
        self.vetores.append(embeddings(pergunta)[0])
        self.respostas.append(resposta)

    def estatisticas(self) -> dict:
        total = sum(self.stats.values()) or 1
        return {**self.stats, "taxa_acerto": round((self.stats["exato"] + self.stats["semantico"]) / total, 3)}
'''),

    ("tarefa",
     "**Teste o cache.** Crie `CacheRespostas(limiar=0.9)`, guarde 2 respostas e busque: a mesma pergunta, uma "
     "variação de maiúsculas/espaços e uma pergunta nova. Mostre as estatísticas.",
     r'''from PKG.cache import CacheRespostas
cache = CacheRespostas(limiar=0.9)
cache.guardar("Qual o horário do suporte?", "Segunda a sexta, das 8h às 20h.")
cache.guardar("O app funciona sem internet?", "Sim, sincroniza quando a conexão volta.")
for q in ("Qual o horário do suporte?", "  qual o HORÁRIO do suporte? ", "Como exporto meus dados?"):
    print(cache.buscar(q), "|", q)
cache.estatisticas()'''),

    ("tarefa",
     "**Memória do KV cache.** Para cada token, cada camada guarda K e V: "
     "`2 × camadas × cabeças_kv × dim_cabeça × bytes`. Para um modelo tipo 8B (32 camadas, 8 cabeças KV, dimensão "
     "128, fp16), calcule a memória do KV cache para contexto de 8.192 tokens e lotes de 1, 16 e 64 requisições.",
     r'''camadas, kv, dim, b = 32, 8, 128, 2
por_token = 2 * camadas * kv * dim * b
for lote in (1, 16, 64):
    gb = por_token * 8192 * lote / 1e9
    print(f"lote {lote:2}: {gb:6.1f} GB  ({por_token / 1024:.0f} KB por token)")'''),

    ("tarefa",
     "**Limitado por memória ou por cálculo?** Uma GPU de exemplo faz 312 TFLOP/s e lê 2 TB/s da memória; o ponto "
     "de virada é `312e12 / 2e12` FLOPs por byte. No *decode* com lote 1 de um modelo de 8B em fp16, cada token faz "
     "~`2 × 8e9` FLOPs e lê ~`8e9 × 2` bytes. Calcule a intensidade aritmética para lotes de 1 a 256 e veja a partir "
     "de qual lote o decode deixa de ser limitado por memória. É por isso que servidores juntam requisições em lotes.",
     r'''virada = 312e12 / 2e12
params = 8e9
for lote in (1, 8, 32, 128, 156, 256):
    flops = 2 * params * lote          # os mesmos pesos servem ao lote inteiro
    bytes_lidos = params * 2           # os pesos são lidos uma vez por passo
    intensidade = flops / bytes_lidos
    limite = "memória" if intensidade < virada else "cálculo"
    print(f"lote {lote:3}: {intensidade:6.0f} FLOP/byte -> limitado por {limite}")
print("ponto de virada:", virada)'''),

    ("tarefa",
     "**Decodificação especulativa.** Um modelo pequeno propõe `k` tokens e o grande confere todos de uma vez. Se "
     "cada token é aceito com probabilidade `α`, o número esperado de tokens por passo do modelo grande é "
     "`(1 - α^(k+1)) / (1 - α)`. Monte a tabela para α = 0,6, 0,8 e 0,9 e k = 2, 4 e 8. Depois **simule** α=0,8, "
     "k=4 com sorteios e confira a fórmula.",
     r'''tabela = pd.DataFrame({f"k={k}": {f"α={a}": (1 - a ** (k + 1)) / (1 - a) for a in (0.6, 0.8, 0.9)}
                       for k in (2, 4, 8)}).round(2)
display(tabela)
rng = np.random.default_rng(0)
def um_passo(a, k):
    aceitos = 0
    while aceitos < k and rng.random() < a:
        aceitos += 1
    return aceitos + 1                  # o grande sempre gera mais 1 token (correção ou continuação)
print("simulado:", np.mean([um_passo(0.8, 4) for _ in range(20000)]).round(2),
      "| fórmula:", round((1 - 0.8 ** 5) / 0.2, 2))'''),
]
