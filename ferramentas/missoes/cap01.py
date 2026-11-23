TITULO = "Sua primeira aplicação de IA"
MISSAO = (
    "Colocar um modelo para responder de verdade, medir **quanto custa** e **quanto demora**, e decidir com números se "
    "um caso de uso vale a pena. É o primeiro tijolo do projeto do curso: o **assistente de suporte da Nimbus**, uma "
    "empresa fictícia de software (os dados dela estão em `comum/dados.py`)."
)
ENTREGA = "o módulo `PKG/nucleo.py`, que responde uma pergunta e devolve texto, latência e tokens; e uma planilha de viabilidade de casos de uso."
LEITURA = [("From Foundation Models to AI Engineering", 36), ("Planning AI Applications (Use Case Evaluation)", 52),
           ("The AI Engineering Stack: Three Layers", 59)]

PASSOS = [
    ("texto",
     "## Ideia em 30 segundos\n"
     "Engenharia de IA é construir produtos **em cima** de modelos prontos (modelos de base), em vez de treinar um "
     "modelo do zero. O trabalho muda de lugar: sai a modelagem e entram avaliação, *prompts*, contexto (RAG), custo, "
     "latência e experiência do usuário. A pilha tem três camadas:\n"
     "1. **aplicação** (prompt, contexto, interface, avaliação);\n"
     "2. **modelo** (escolha, ajuste fino, dados);\n"
     "3. **infraestrutura** (servir, escalar, monitorar).\n\n"
     "Neste curso você trabalha quase sempre na camada de aplicação, que é onde está a maior parte das vagas."),

    ("tarefa",
     "**Primeira chamada.** Use `perguntar` para pedir, em 2 frases, uma explicação do que faz um engenheiro de IA. "
     "Mostre a resposta e depois `gasto()`.",
     r'''resposta = perguntar("Em 2 frases, o que faz um engenheiro de IA?")
print(resposta)
print(gasto())'''),

    ("tarefa",
     "**Anatomia da resposta.** Com `conversar`, mande uma mensagem de sistema (\"Você é o suporte da Nimbus, responda "
     "em uma frase.\") e uma do usuário. Mostre: o modelo usado, o motivo de parada (`finish_reason`), os tokens de "
     "entrada e de saída (`usage`) e o texto.",
     r'''r = conversar([
    {"role": "system", "content": "Você é o suporte da Nimbus, responda em uma frase."},
    {"role": "user", "content": "Vocês têm aplicativo para celular?"},
])
print("modelo:", r.model, "| parada:", r.choices[0].finish_reason)
print("tokens:", r.usage.prompt_tokens, "entrada,", r.usage.completion_tokens, "saída")
print(r.choices[0].message.content)'''),

    ("tarefa",
     "**Latência.** Meça com `time.perf_counter()` o tempo de 3 chamadas iguais e mostre a média e a maior. "
     "Por que as três não demoram o mesmo?",
     r'''tempos = []
for _ in range(3):
    t0 = time.perf_counter()
    perguntar("Diga apenas: ok")
    tempos.append(time.perf_counter() - t0)
print(f"média {np.mean(tempos):.2f}s | maior {max(tempos):.2f}s")
# a rede, a fila do provedor e o tamanho da resposta variam a cada chamada'''),

    ("tarefa",
     "**Quanto custa por mês?** Escreva `custo_mensal(chamadas_dia, tokens_in, tokens_out, preco_in, preco_out)`, com os "
     "preços em US$ por **1 milhão** de tokens. Calcule para o suporte da Nimbus: 2.000 chamados por dia, ~800 tokens "
     "de entrada e ~250 de saída, comparando o `gpt-4o-mini` (0,15 / 0,60) com o `gpt-4o` (2,50 / 10,00). "
     "Os preços mudam: confira no site do OpenRouter quando for decidir de verdade.",
     r'''def custo_mensal(chamadas_dia, tokens_in, tokens_out, preco_in, preco_out, dias=30):
    por_chamada = tokens_in / 1e6 * preco_in + tokens_out / 1e6 * preco_out
    return chamadas_dia * dias * por_chamada

for nome, pin, pout in [("gpt-4o-mini", 0.15, 0.60), ("gpt-4o", 2.50, 10.00)]:
    print(f"{nome:12} US$ {custo_mensal(2000, 800, 250, pin, pout):8.2f} por mês")'''),

    ("tarefa",
     "**Vale a pena?** Monte um `DataFrame` com 4 casos de uso candidatos da Nimbus (por exemplo: responder chamados, "
     "resumir reuniões, gerar relatórios para gestores, traduzir a central de ajuda). Dê notas de 1 a 5 para: "
     "`valor` para o negócio, `risco` de erro (5 = baixo risco), `dados` disponíveis e `medir` (facilidade de medir o "
     "sucesso). Calcule uma nota ponderada (pesos à sua escolha) e ordene. Qual você faria primeiro?",
     r'''casos = pd.DataFrame([
    {"caso": "responder chamados", "valor": 5, "risco": 3, "dados": 5, "medir": 4},
    {"caso": "resumir reuniões", "valor": 3, "risco": 4, "dados": 3, "medir": 2},
    {"caso": "relatórios para gestores", "valor": 4, "risco": 2, "dados": 4, "medir": 3},
    {"caso": "traduzir central de ajuda", "valor": 2, "risco": 5, "dados": 5, "medir": 4},
])
pesos = {"valor": 0.4, "risco": 0.2, "dados": 0.2, "medir": 0.2}
casos["nota"] = sum(casos[c] * p for c, p in pesos.items())
casos.sort_values("nota", ascending=False)'''),

    ("tarefa",
     "**Metas antes de construir.** Defina num dicionário 3 metas mensuráveis para o assistente (por exemplo: % de "
     "respostas corretas, latência máxima, custo máximo por chamado) e mostre como uma tabela. Você vai medir essas "
     "metas nos capítulos 4 e 10.",
     r'''metas = {
    "respostas corretas (nota do juiz >= 4)": ">= 85%",
    "latência p90": "<= 4 s",
    "custo por chamado": "<= US$ 0,001",
}
pd.Series(metas, name="meta").to_frame()'''),

    ("arquivo",
     "**Primeiro módulo do projeto.** Escreva `nucleo.py` com:\n"
     "- `SISTEMA`: o texto de sistema do assistente da Nimbus (tom educado, respostas curtas, admitir quando não sabe);\n"
     "- `responder(pergunta, sistema=SISTEMA, modelo=MODELO)`: chama o modelo e devolve um dicionário com `texto`, "
     "`latencia_s`, `tokens_in`, `tokens_out` e `modelo`.",
     "nucleo.py",
     r'''"""Núcleo do assistente da Nimbus: uma chamada ao modelo com medição."""
import time

from ia import MODELO, conversar

SISTEMA = ("Você é o assistente de suporte da Nimbus, um aplicativo de gestão de tarefas para equipes. "
           "Responda em português, com educação e no máximo 3 frases. "
           "Se não tiver certeza da resposta, diga que vai encaminhar para um atendente.")


def responder(pergunta: str, sistema: str = SISTEMA, modelo: str = MODELO) -> dict:
    t0 = time.perf_counter()
    r = conversar([{"role": "system", "content": sistema}, {"role": "user", "content": pergunta}], modelo=modelo)
    return {
        "texto": r.choices[0].message.content,
        "latencia_s": round(time.perf_counter() - t0, 3),
        "tokens_in": r.usage.prompt_tokens,
        "tokens_out": r.usage.completion_tokens,
        "modelo": modelo,
    }
'''),

    ("tarefa",
     "**Teste o núcleo.** Rode `responder` nas 3 primeiras perguntas de `PERGUNTAS` e mostre um `DataFrame` com a "
     "pergunta, o texto (cortado em 80 caracteres), a latência e os tokens. As respostas estão certas? (Por enquanto "
     "o modelo **não conhece** a Nimbus: ele vai inventar ou dizer que não sabe. O RAG do capítulo 6 resolve isso.)",
     r'''from PKG.nucleo import responder
linhas = []
for p in PERGUNTAS[:3]:
    r = responder(p["pergunta"])
    linhas.append({"pergunta": p["pergunta"], "resposta": r["texto"][:80], "latencia_s": r["latencia_s"],
                   "tokens": r["tokens_in"] + r["tokens_out"]})
pd.DataFrame(linhas)'''),
]
