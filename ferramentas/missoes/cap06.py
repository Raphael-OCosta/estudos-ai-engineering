TITULO = "RAG e agentes"
MISSAO = (
    "Dar ao assistente o conhecimento da Nimbus com **RAG**. Você vai:\n"
    "- quebrar os documentos em pedaços;\n"
    "- buscar por palavras (BM25) e por sentido (embeddings);\n"
    "- combinar as duas buscas (RRF) e medir a recuperação (recall@k, MRR);\n"
    "- responder com citações.\n\n"
    "Depois, um **agente** que usa ferramentas (calcular preço, consultar a documentação) num laço de raciocínio, e "
    "uma **memória** de conversa. No fim, você compara com a linha de base do capítulo 4 e vê o salto."
)
ENTREGA = "os módulos `PKG/rag.py` (base de conhecimento com busca híbrida e resposta com fontes) e `PKG/agente.py` (agente com ferramentas)."
LEITURA = [("RAG Architecture", 280), ("Retrieval Algorithms", 281), ("Retrieval Optimization", 291),
           ("Agent Overview e Tools", 300), ("Planning", 305), ("Agent Failure Modes and Evaluation", 322),
           ("Memory", 324)]

PASSOS = [
    ("texto",
     "## Ideia em 30 segundos\n"
     "**RAG** = buscar os trechos certos e colocá-los no prompt. A qualidade do RAG depende mais da **busca** que do "
     "modelo:\n"
     "- BM25 é ótimo para termos exatos (\"NIM-123\", \"SSO\");\n"
     "- embeddings acham o sentido mesmo com outras palavras;\n"
     "- a busca híbrida junta os dois.\n\n"
     "Um **agente** é um modelo num laço: ele planeja, chama ferramentas, lê o resultado e decide o próximo passo, "
     "até responder."),

    ("tarefa",
     "**Pedaços (chunks).** Quebre cada documento em pedaços de **2 frases**, com sobreposição de 1 frase (a última "
     "frase de um pedaço é a primeira do próximo). Guarde dicts com `doc`, `titulo` e `texto`. Quantos pedaços saíram?",
     r'''def pedacos_de(doc, frases_por_pedaco=2, sobreposicao=1):
    frases = [f.strip() for f in re.split(r"(?<=[.!?])\s+", doc["texto"]) if f.strip()]
    passo = frases_por_pedaco - sobreposicao
    saida = []
    for i in range(0, max(1, len(frases) - sobreposicao), passo):
        saida.append({"doc": doc["id"], "titulo": doc["titulo"], "texto": " ".join(frases[i:i + frases_por_pedaco])})
    return saida

PEDACOS = [p for d in DOCUMENTOS for p in pedacos_de(d)]
print(len(PEDACOS), "pedaços")
PEDACOS[:3]'''),

    ("tarefa",
     "**Busca por palavras (BM25).** Use `rank_bm25.BM25Okapi` com os textos tokenizados (minúsculas, só palavras). "
     "Escreva `buscar_bm25(pergunta, k=3)`, que devolve os índices dos k melhores pedaços, e teste com \"Como ligo "
     "commits às tarefas?\".",
     r'''from rank_bm25 import BM25Okapi

def tokenizar(t):
    return re.findall(r"\w+", t.lower())

bm25 = BM25Okapi([tokenizar(p["titulo"] + " " + p["texto"]) for p in PEDACOS])

def buscar_bm25(pergunta, k=3):
    notas = bm25.get_scores(tokenizar(pergunta))
    return list(np.argsort(notas)[::-1][:k])

for i in buscar_bm25("Como ligo commits às tarefas?"):
    print(PEDACOS[i]["doc"], "|", PEDACOS[i]["texto"][:90])'''),

    ("tarefa",
     "**Busca por sentido (embeddings).** Calcule os vetores de todos os pedaços **uma vez** (`VETORES`). Escreva "
     "`buscar_vetor(pergunta, k=3)` com similaridade de cosseno e teste com uma pergunta que não usa as palavras do "
     "documento: \"Dá para mexer nas tarefas no avião?\".",
     r'''VETORES = embeddings([p["titulo"] + ". " + p["texto"] for p in PEDACOS])

def buscar_vetor(pergunta, k=3):
    notas = similaridade(embeddings(pergunta)[0], VETORES)[0]
    return list(np.argsort(notas)[::-1][:k])

for i in buscar_vetor("Dá para mexer nas tarefas no avião?"):
    print(PEDACOS[i]["doc"], "|", PEDACOS[i]["texto"][:90])'''),

    ("tarefa",
     "**Meça a recuperação.** Para cada item de `PERGUNTAS`, veja se o `doc` certo aparece nos 3 primeiros pedaços "
     "(**recall@3**) e em que posição aparece pela primeira vez (**MRR** = média de 1/posição). Compare BM25 e "
     "embeddings.",
     r'''def medir_busca(buscar, k=3):
    acertos, rr = 0, []
    for item in PERGUNTAS:
        docs = [PEDACOS[i]["doc"] for i in buscar(item["pergunta"], k)]
        acertos += item["doc"] in docs
        rr.append(1 / (docs.index(item["doc"]) + 1) if item["doc"] in docs else 0)
    return {"recall@k": round(acertos / len(PERGUNTAS), 3), "MRR": round(float(np.mean(rr)), 3)}

print("BM25:      ", medir_busca(buscar_bm25))
print("embeddings:", medir_busca(buscar_vetor))'''),

    ("tarefa",
     "**Busca híbrida com RRF.** Junte as duas listas com *Reciprocal Rank Fusion*: cada pedaço ganha "
     "`1 / (60 + posição)` em cada lista em que aparece (posição começando em 1). Busque 10 em cada método, some e "
     "devolva os k melhores. Meça de novo.",
     r'''def buscar_hibrida(pergunta, k=3, c=60):
    pontos = {}
    for lista in (buscar_bm25(pergunta, 10), buscar_vetor(pergunta, 10)):
        for pos, i in enumerate(lista, start=1):
            pontos[i] = pontos.get(i, 0) + 1 / (c + pos)
    return sorted(pontos, key=pontos.get, reverse=True)[:k]

print("híbrida:", medir_busca(buscar_hibrida))'''),

    ("tarefa",
     "**Reescrita da consulta.** Clientes escrevem de jeito informal. Peça ao modelo para reescrever \"to travado "
     "nao consigo logar ajuda\" como uma consulta de busca objetiva e compare os pedaços recuperados antes e depois.",
     r'''original = "to travado nao consigo logar ajuda"
reescrita = perguntar(f"Reescreva como uma consulta de busca objetiva para a central de ajuda, em uma linha: {original}",
                      temperature=0)
print("reescrita:", reescrita)
for consulta in (original, reescrita):
    print([PEDACOS[i]["doc"] for i in buscar_hibrida(consulta)])'''),

    ("arquivo",
     "**Módulo de RAG.** Escreva `rag.py` com a classe `BaseConhecimento(documentos)`:\n"
     "- `__init__`: cria os pedaços, o BM25 e os vetores;\n"
     "- `buscar(pergunta, k=3)`: busca híbrida com RRF, devolve a lista de pedaços;\n"
     "- `responder(pergunta, modelo=MODELO)`: monta o prompt com os pedaços numerados `[1]`, `[2]`..., manda o "
     "modelo usar **só** esse contexto e citar os números, e devolve o mesmo dict do `nucleo` (texto, latência, "
     "tokens, modelo) mais `fontes` (ids dos documentos).",
     "rag.py",
     r'''"""RAG da Nimbus: pedaços, busca híbrida (BM25 + embeddings, RRF) e resposta com citações."""
import re
import time

import numpy as np
from rank_bm25 import BM25Okapi

from ia import MODELO, conversar, embeddings, similaridade

SISTEMA = ("Você é o assistente de suporte da Nimbus. Responda em português, em no máximo 3 frases, usando SOMENTE "
           "o contexto. Cite as fontes com [n]. Se o contexto não tiver a resposta, diga que vai encaminhar para "
           "um atendente.")


def _tokenizar(t):
    return re.findall(r"\w+", t.lower())


def _pedacos(doc, n=2, sobreposicao=1):
    frases = [f.strip() for f in re.split(r"(?<=[.!?])\s+", doc["texto"]) if f.strip()]
    passo = n - sobreposicao
    return [{"doc": doc["id"], "titulo": doc["titulo"], "texto": " ".join(frases[i:i + n])}
            for i in range(0, max(1, len(frases) - sobreposicao), passo)]


class BaseConhecimento:
    def __init__(self, documentos):
        self.pedacos = [p for d in documentos for p in _pedacos(d)]
        textos = [p["titulo"] + ". " + p["texto"] for p in self.pedacos]
        self.bm25 = BM25Okapi([_tokenizar(t) for t in textos])
        self.vetores = embeddings(textos)

    def _bm25(self, pergunta, k):
        return list(np.argsort(self.bm25.get_scores(_tokenizar(pergunta)))[::-1][:k])

    def _vetor(self, pergunta, k):
        notas = similaridade(embeddings(pergunta)[0], self.vetores)[0]
        return list(np.argsort(notas)[::-1][:k])

    def buscar(self, pergunta: str, k: int = 3, c: int = 60) -> list[dict]:
        pontos = {}
        for lista in (self._bm25(pergunta, 10), self._vetor(pergunta, 10)):
            for pos, i in enumerate(lista, start=1):
                pontos[i] = pontos.get(i, 0) + 1 / (c + pos)
        return [self.pedacos[i] for i in sorted(pontos, key=pontos.get, reverse=True)[:k]]

    def responder(self, pergunta: str, modelo: str = MODELO, k: int = 3) -> dict:
        t0 = time.perf_counter()
        pedacos = self.buscar(pergunta, k)
        contexto = "\n".join(f"[{n}] ({p['titulo']}) {p['texto']}" for n, p in enumerate(pedacos, start=1))
        r = conversar([{"role": "system", "content": SISTEMA},
                       {"role": "user", "content": f"Contexto:\n{contexto}\n\nPergunta: {pergunta}"}],
                      modelo=modelo, temperature=0)
        return {"texto": r.choices[0].message.content, "latencia_s": round(time.perf_counter() - t0, 3),
                "tokens_in": r.usage.prompt_tokens, "tokens_out": r.usage.completion_tokens, "modelo": modelo,
                "fontes": list(dict.fromkeys(p["doc"] for p in pedacos))}
'''),

    ("tarefa",
     "**O salto do RAG.** Crie `base = BaseConhecimento(DOCUMENTOS)`, responda 2 perguntas mostrando as fontes e "
     "depois avalie `base.responder` nas mesmas 8 perguntas do capítulo 4 com `PKG.avaliacao`. Compare com "
     "`../saidas/base_cap04.csv`.",
     r'''from PKG.rag import BaseConhecimento
from PKG.avaliacao import avaliar, resumo
base = BaseConhecimento(DOCUMENTOS)
for p in ("Posso exportar em JSON no plano grátis?", "Quanto tempo vale o link de troca de senha?"):
    r = base.responder(p)
    print(r["fontes"], "|", r["texto"])
com_rag = avaliar(base.responder, PERGUNTAS[:8])
sem_rag = pd.read_csv("../saidas/base_cap04.csv")
pd.DataFrame({"sem RAG (cap. 4)": resumo(sem_rag), "com RAG": resumo(com_rag)})'''),

    ("texto",
     "## Agentes\n"
     "O modelo recebe a descrição das **ferramentas** (nome, para que serve, parâmetros em JSON Schema). Quando "
     "precisa, ele devolve um pedido de chamada (`tool_calls`) em vez de texto. O seu código executa a ferramenta, "
     "devolve o resultado numa mensagem `role=\"tool\"` e chama o modelo de novo, até ele responder.\n\n"
     "Os erros mais comuns de um agente são:\n"
     "- ferramenta errada;\n"
     "- argumentos inválidos;\n"
     "- laço infinito.\n\n"
     "Por isso sempre há um **limite de passos** e um registro (*trace*) de tudo."),

    ("tarefa",
     "**Ferramentas.** Escreva duas funções Python:\n"
     "- `calcular_preco(plano, usuarios, anual)`, com preços por usuário por mês: Equipe 29 e Empresa 59; o "
     "pagamento anual tem 20% de desconto; o Grátis custa 0;\n"
     "- `buscar_documentacao(consulta)`, que devolve o texto dos 2 pedaços mais relevantes da `base`.\n\n"
     "Escreva também a lista `FERRAMENTAS` no formato da API (`type: function`, `name`, `description`, `parameters`).",
     r'''def calcular_preco(plano: str, usuarios: int, anual: bool = False) -> dict:
    por_usuario = {"gratis": 0, "equipe": 29, "empresa": 59}[plano.lower().replace("á", "a")]
    mensal = por_usuario * usuarios
    total_ano = mensal * 12 * (0.8 if anual else 1)
    return {"plano": plano, "usuarios": usuarios, "mensal": mensal, "total_ano": round(total_ano, 2)}

def buscar_documentacao(consulta: str) -> str:
    return "\n".join(p["texto"] for p in base.buscar(consulta, k=2))

FERRAMENTAS = [
    {"type": "function", "function": {
        "name": "buscar_documentacao", "description": "Busca trechos da central de ajuda da Nimbus.",
        "parameters": {"type": "object", "properties": {"consulta": {"type": "string"}}, "required": ["consulta"]}}},
    {"type": "function", "function": {
        "name": "calcular_preco", "description": "Calcula o preço de um plano (gratis, equipe ou empresa).",
        "parameters": {"type": "object", "properties": {
            "plano": {"type": "string", "enum": ["gratis", "equipe", "empresa"]},
            "usuarios": {"type": "integer"}, "anual": {"type": "boolean"}},
            "required": ["plano", "usuarios", "anual"]}}},
]
print(calcular_preco("empresa", 12, anual=True))'''),

    ("arquivo",
     "**Módulo do agente.** Escreva `agente.py` com `executar_agente(pergunta, ferramentas, funcoes, max_passos=5)`:\n"
     "1. começa com um sistema que manda usar ferramentas quando precisar de dados;\n"
     "2. a cada passo chama `conversar(..., tools=ferramentas)`;\n"
     "3. se vierem `tool_calls`, executa cada uma (`funcoes[nome](**args)`), captura erros como texto e devolve com "
     "`role=\"tool\"` e `tool_call_id`;\n"
     "4. se vier texto, termina.\n\n"
     "Devolve `{\"resposta\": ..., \"passos\": [trace]}`. Se estourar `max_passos`, devolve uma mensagem de desistência.",
     "agente.py",
     r'''"""Agente com ferramentas: o modelo decide, o código executa, até a resposta final."""
import json

from ia import MODELO, conversar

SISTEMA = ("Você é o assistente da Nimbus. Use as ferramentas sempre que precisar de dados (preços, regras). "
           "Responda em português, de forma curta, só depois de ter os dados.")


def executar_agente(pergunta: str, ferramentas: list, funcoes: dict, modelo: str = MODELO, max_passos: int = 5) -> dict:
    mensagens = [{"role": "system", "content": SISTEMA}, {"role": "user", "content": pergunta}]
    trace = []
    for passo in range(1, max_passos + 1):
        r = conversar(mensagens, modelo=modelo, tools=ferramentas, temperature=0)
        msg = r.choices[0].message
        if not msg.tool_calls:
            trace.append({"passo": passo, "tipo": "resposta"})
            return {"resposta": msg.content, "passos": trace}
        mensagens.append({"role": "assistant", "content": msg.content, "tool_calls": [
            {"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}}
            for c in msg.tool_calls]})
        for chamada in msg.tool_calls:
            nome = chamada.function.name
            try:
                args = json.loads(chamada.function.arguments or "{}")
                resultado = funcoes[nome](**args)
            except Exception as erro:          # o erro vira informação para o modelo se corrigir
                args, resultado = {}, f"ERRO: {type(erro).__name__}: {erro}"
            trace.append({"passo": passo, "tipo": "ferramenta", "nome": nome, "args": args,
                          "resultado": str(resultado)[:200]})
            mensagens.append({"role": "tool", "tool_call_id": chamada.id,
                              "content": json.dumps(resultado, ensure_ascii=False, default=str)})
    return {"resposta": "Não consegui concluir dentro do limite de passos; vou encaminhar para um atendente.",
            "passos": trace}
'''),

    ("tarefa",
     "**Rode o agente.** Pergunte \"Quanto uma equipe de 12 pessoas pagaria por ano no plano Empresa pagando "
     "anual? E tem SSO?\". Mostre a resposta e o *trace* como tabela. Ele usou as duas ferramentas? (No modo "
     "simulado as chamadas são falsas e podem dar erro de argumento: veja como o erro vira texto para o modelo.)",
     r'''from PKG.agente import executar_agente
saida = executar_agente("Quanto uma equipe de 12 pessoas pagaria por ano no plano Empresa pagando anual? E tem SSO?",
                        FERRAMENTAS, {"calcular_preco": calcular_preco, "buscar_documentacao": buscar_documentacao})
print(saida["resposta"])
pd.DataFrame(saida["passos"])'''),

    ("tarefa",
     "**Memória de conversa.** Escreva a classe `MemoriaResumida(max_mensagens=4)`: guarda as mensagens. Quando "
     "passar do limite, junta as mais antigas num **resumo** (feito pelo modelo) e mantém só as últimas. O método "
     "`contexto()` devolve a lista para mandar ao modelo (o resumo como mensagem de sistema + as recentes). Simule 6 "
     "trocas e mostre o contexto final.",
     r'''class MemoriaResumida:
    def __init__(self, max_mensagens=4):
        self.max = max_mensagens
        self.resumo = ""
        self.mensagens = []

    def adicionar(self, papel, texto):
        self.mensagens.append({"role": papel, "content": texto})
        if len(self.mensagens) > self.max:
            antigas, self.mensagens = self.mensagens[:-self.max], self.mensagens[-self.max:]
            conversa = "\n".join(f"{m['role']}: {m['content']}" for m in antigas)
            self.resumo = perguntar(f"Resumo anterior: {self.resumo}\nNovas mensagens:\n{conversa}\n"
                                    "Atualize o resumo em até 3 frases, guardando fatos do cliente.", temperature=0)

    def contexto(self):
        topo = [{"role": "system", "content": f"Resumo da conversa até aqui: {self.resumo}"}] if self.resumo else []
        return topo + self.mensagens

mem = MemoriaResumida()
for i, fala in enumerate(["Oi, sou a Ana da empresa Lumen.", "Temos 15 pessoas.", "Usamos o plano Equipe.",
                          "Queremos SSO.", "Quanto custaria mudar?", "E o desconto anual?"]):
    mem.adicionar("user", fala)
    mem.adicionar("assistant", f"(resposta {i + 1})")
mem.contexto()'''),
]
