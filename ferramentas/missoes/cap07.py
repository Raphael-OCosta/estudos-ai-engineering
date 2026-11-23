TITULO = "Ajuste fino (finetuning) sem GPU"
MISSAO = (
    "Entender o ajuste fino pela **matemática que decide se ele cabe no seu bolso**. Você vai calcular memória de "
    "inferência e de treino, ver os formatos numéricos e a quantização na prática, contar parâmetros de LoRA, "
    "**treinar um LoRA de verdade em NumPy**, fundir modelos e preparar um conjunto de treino no formato que as APIs "
    "de ajuste fino aceitam. Antes disso, uma regra para decidir entre RAG e ajuste fino."
)
ENTREGA = "um LoRA treinado à mão (você vê a perda cair com 3% dos parâmetros) e o arquivo `saidas/treino.jsonl`, pronto para um ajuste fino real."
LEITURA = [("When to Finetune (Finetuning and RAG)", 335), ("Memory Math", 346), ("Numerical Representations", 349),
           ("Quantization", 352), ("Parameter-Efficient Finetuning (LoRA)", 356), ("Model Merging", 371)]

PASSOS = [
    ("texto",
     "## Ideia em 30 segundos\n"
     "Ajuste fino muda os **pesos** do modelo. RAG muda o **contexto**.\n"
     "- Use RAG quando falta **informação** (fatos, documentos que mudam).\n"
     "- Use ajuste fino quando falta **comportamento**: formato, estilo, uma tarefa estreita repetida milhões de "
     "vezes, ou um modelo menor e mais barato fazendo o que um grande faz.\n\n"
     "O gargalo do ajuste fino é a **memória**, e é por isso que existem LoRA e quantização."),

    ("tarefa",
     "**RAG ou ajuste fino?** Escreva `recomendar(caso)` com regras simples a partir de um dict com `falta` "
     "(`\"informacao\"` ou `\"comportamento\"`), `muda_rapido` (bool) e `volume_alto` (bool). Aplique a 4 cenários da "
     "Nimbus e explique cada resultado.",
     r'''def recomendar(caso):
    if caso["falta"] == "informacao" or caso["muda_rapido"]:
        return "RAG"
    if caso["volume_alto"]:
        return "ajuste fino (de um modelo menor)"
    return "prompt + exemplos (few-shot) primeiro"

cenarios = {
    "preços e regras da central de ajuda": {"falta": "informacao", "muda_rapido": True, "volume_alto": True},
    "responder sempre no formato JSON da empresa": {"falta": "comportamento", "muda_rapido": False, "volume_alto": True},
    "tom de voz da marca em e-mails raros": {"falta": "comportamento", "muda_rapido": False, "volume_alto": False},
    "classificar 1 milhão de chamados por mês": {"falta": "comportamento", "muda_rapido": False, "volume_alto": True},
}
pd.Series({nome: recomendar(c) for nome, c in cenarios.items()}, name="recomendação").to_frame()'''),

    ("tarefa",
     "**Memória para inferência.** Os pesos ocupam `parâmetros × bytes por parâmetro`. Monte uma tabela em GB para "
     "modelos de 7, 13 e 70 bilhões de parâmetros em fp32 (4 bytes), fp16/bf16 (2), int8 (1) e int4 (0,5). Qual "
     "deles cabe numa GPU de 24 GB?",
     r'''bytes_por = {"fp32": 4, "fp16/bf16": 2, "int8": 1, "int4": 0.5}
tabela = pd.DataFrame({fmt: {f"{n}B": n * 1e9 * b / 1e9 for n in (7, 13, 70)} for fmt, b in bytes_por.items()})
print("GB só para os pesos:")
tabela.round(1)'''),

    ("tarefa",
     "**Memória para treino.** No treino completo com Adam em fp16, uma conta aproximada por parâmetro treinável é: "
     "pesos (2 bytes) + gradientes (2) + estados do Adam (2 × 4 bytes, em fp32) = 12 bytes, sem contar as ativações. "
     "Calcule para um modelo de 7B com ajuste completo e com LoRA (só ~0,5% dos parâmetros treináveis; o resto fica "
     "congelado, só os 2 bytes do peso).",
     r'''P = 7e9
completo = P * 12 / 1e9
treinaveis = P * 0.005
lora = (P * 2 + treinaveis * (2 + 2 + 8)) / 1e9
print(f"ajuste completo: ~{completo:.0f} GB (+ ativações)")
print(f"LoRA:            ~{lora:.0f} GB (+ ativações)")'''),

    ("tarefa",
     "**Formatos numéricos.** Mostre na prática:\n"
     "1. `0.1 + 0.2` em float32 e float16;\n"
     "2. que 70.000 não cabe em float16 (vira `inf`);\n"
     "3. que o bfloat16 aguenta o número grande, mas perde precisão.\n\n"
     "Para simular o bfloat16, zere os 16 bits de baixo de um float32 (`view(np.uint32) & 0xFFFF0000`).",
     r'''print("float32:", np.float32(0.1) + np.float32(0.2), "| float16:", np.float16(0.1) + np.float16(0.2))
print("70000 em float16:", np.float16(70000))

def para_bf16(x):
    a = np.asarray(x, dtype=np.float32)
    return (a.view(np.uint32) & np.uint32(0xFFFF0000)).view(np.float32)

for x in (70000.0, 3.14159265, 0.1):
    print(f"{x:>12} -> bf16 {float(para_bf16(x)):.6f}")'''),

    ("tarefa",
     "**Quantização int8.** Gere uma matriz de pesos 256×256 (`rng.normal(0, 0.02)`) com algumas colunas de escala "
     "maior (multiplique 8 colunas por 10). Quantize para int8:\n"
     "- (a) **por tensor**: uma escala para tudo, `escala = max|W| / 127`;\n"
     "- (b) **por coluna**: uma escala por coluna.\n\n"
     "Desquantize e compare o erro médio absoluto. Por que o (b) ganha?",
     r'''rng = np.random.default_rng(0)
W = rng.normal(0, 0.02, (256, 256)).astype(np.float32)
W[:, :8] *= 10                                         # colunas "fora da curva" (outliers)

def quantizar(W, eixo=None):
    escala = np.abs(W).max(axis=eixo, keepdims=eixo is not None) / 127
    q = np.clip(np.round(W / escala), -127, 127).astype(np.int8)
    return q, escala

for nome, eixo in (("por tensor", None), ("por coluna", 0)):
    q, s = quantizar(W, eixo)
    erro = np.abs(W - q.astype(np.float32) * s).mean()
    print(f"{nome:11} erro médio {erro:.2e} | memória {q.nbytes / 1024:.0f} KB (era {W.nbytes / 1024:.0f} KB)")'''),

    ("tarefa",
     "**Quantos parâmetros o LoRA treina?** Uma camada de 4096×4096 tem `d × k` pesos. O LoRA troca a atualização "
     "por `B (d×r) @ A (r×k)`, ou seja, `r × (d + k)` parâmetros. Calcule para r = 4, 8, 16 e 64 e a fração em "
     "relação à camada inteira.",
     r'''d = k = 4096
linhas = [{"r": r, "parametros_lora": r * (d + k), "fração": r * (d + k) / (d * k)} for r in (4, 8, 16, 64)]
tabela = pd.DataFrame(linhas)
tabela["fração"] = tabela["fração"].map("{:.2%}".format)
tabela'''),

    ("tarefa",
     "**Treine um LoRA em NumPy.** Monte o experimento:\n"
     "- um \"modelo base\" linear congelado `W0` (64×64);\n"
     "- uma tarefa nova cujo modelo ideal é `W0 + ΔW`, com ΔW de posto 2;\n"
     "- os dados: 512 exemplos `X` e `Y = X @ (W0 + ΔW).T`.\n\n"
     "Treine só `A` (2×64, aleatória pequena) e `B` (64×2, zeros) com gradiente descendente na perda MSE de "
     "`X @ (W0 + B@A).T`, por 300 passos (lr=0.003). Mostre a perda a cada 50 passos e quantos parâmetros foram "
     "treinados em comparação com `W0`. Repare no platô do começo: como `B` começa em zero, o LoRA parte "
     "exatamente do modelo base e só depois \"descobre\" a direção da mudança.",
     r'''rng = np.random.default_rng(42)
d, r, n = 64, 2, 512
W0 = rng.normal(0, 0.1, (d, d))
delta = rng.normal(0, 0.3, (d, r)) @ rng.normal(0, 0.3, (r, d))   # mudança de posto 2
X = rng.normal(0, 1, (n, d))
Y = X @ (W0 + delta).T

A = rng.normal(0, 0.01, (r, d))
B = np.zeros((d, r))
lr = 0.003
for passo in range(301):
    erro = X @ (W0 + B @ A).T - Y                 # (n, d)
    perda = (erro ** 2).mean()
    G = 2 * erro.T @ X / (n * d)                  # gradiente da perda em relação a W = W0 + B@A
    gB, gA = G @ A.T, B.T @ G
    B -= lr * gB * d
    A -= lr * gA * d
    if passo % 50 == 0:
        print(f"passo {passo:3}  perda {perda:.5f}")
print(f"treinados: {A.size + B.size} parâmetros | W0 tem {W0.size} ({(A.size + B.size) / W0.size:.1%})")'''),

    ("tarefa",
     "**Fundir modelos (vetores de tarefa).** Com regressão linear simples: um modelo base `θ0` e duas tarefas, cada "
     "uma com o seu modelo ajustado (`θA`, `θB`, por mínimos quadrados a partir de `θ0` com poucos dados). Os "
     "**vetores de tarefa** são `θA - θ0` e `θB - θ0`. Compare o erro nas duas tarefas para: `θ0`, `θA`, `θB`, média "
     "simples `(θA+θB)/2` e soma de vetores de tarefa `θ0 + (θA-θ0) + (θB-θ0)`.",
     r'''rng = np.random.default_rng(1)
p = 20
theta0 = rng.normal(0, 1, p)
alvoA = theta0.copy(); alvoA[:5] += 2          # a tarefa A muda as 5 primeiras coordenadas
alvoB = theta0.copy(); alvoB[5:10] -= 2        # a tarefa B muda as 5 seguintes

def dados(alvo, n=200):
    X = rng.normal(0, 1, (n, p))
    return X, X @ alvo + rng.normal(0, 0.1, n)

XA, yA = dados(alvoA); XB, yB = dados(alvoB)
thetaA = np.linalg.lstsq(XA, yA, rcond=None)[0]
thetaB = np.linalg.lstsq(XB, yB, rcond=None)[0]
erro = lambda th, X, y: float(np.mean((X @ th - y) ** 2))
candidatos = {"base": theta0, "só A": thetaA, "só B": thetaB, "média": (thetaA + thetaB) / 2,
              "soma de vetores": theta0 + (thetaA - theta0) + (thetaB - theta0)}
pd.DataFrame({nome: {"erro tarefa A": erro(th, XA, yA), "erro tarefa B": erro(th, XB, yB)}
              for nome, th in candidatos.items()}).T.round(3)'''),

    ("tarefa",
     "**Dados para um ajuste fino real.** Transforme os `TICKETS` no formato de conversa das APIs de ajuste fino: uma "
     "linha JSON por exemplo, `{\"messages\": [sistema, usuário, assistente]}`, em que o assistente responde só a "
     "categoria. Valide (3 mensagens, papéis certos, conteúdo não vazio), separe 80/20 em treino/validação com "
     "semente fixa e grave `../saidas/treino.jsonl` e `../saidas/validacao.jsonl`. Mostre o total de tokens.",
     r'''SISTEMA_FT = "Classifique o chamado da Nimbus em: " + ", ".join(CATEGORIAS) + ". Responda só a categoria."
exemplos = [{"messages": [{"role": "system", "content": SISTEMA_FT}, {"role": "user", "content": t},
                          {"role": "assistant", "content": c}]} for t, c in TICKETS]

def valido(ex):
    m = ex["messages"]
    return len(m) == 3 and [x["role"] for x in m] == ["system", "user", "assistant"] and all(x["content"].strip() for x in m)

assert all(valido(e) for e in exemplos)
ordem = np.random.default_rng(0).permutation(len(exemplos))
corte = int(0.8 * len(exemplos))
for nome, idx in (("treino", ordem[:corte]), ("validacao", ordem[corte:])):
    with open(f"../saidas/{nome}.jsonl", "w", encoding="utf-8") as f:
        for i in idx:
            f.write(json.dumps(exemplos[i], ensure_ascii=False) + "\n")
tokens = sum(contar_tokens(m["content"]) for e in exemplos for m in e["messages"])
print(f"{corte} treino, {len(exemplos) - corte} validação, {tokens} tokens no total")'''),

    ("texto",
     "## E para treinar de verdade?\n"
     "- **Pela API** (o mais simples): o OpenAI e outros provedores aceitam esse `.jsonl` e cobram por token de "
     "treino. Comece com 50 a 100 exemplos bons, avalie com o pipeline do capítulo 4 e só então aumente.\n"
     "- **Num modelo aberto**: bibliotecas como Hugging Face PEFT/TRL ou Unsloth treinam LoRA/QLoRA numa GPU de "
     "consumidor (ou no Google Colab). O LoRA que você treinou em NumPy é exatamente a mesma ideia, só que dentro de "
     "cada camada de atenção."),
]
