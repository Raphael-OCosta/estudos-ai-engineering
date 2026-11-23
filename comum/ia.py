"""Acesso aos modelos para a trilha prática do AI Engineering (Chip Huyen).

Os cadernos fazem `from ia import *` na Preparação. Você não precisa mexer aqui, mas vale ler:
é um exemplo real de "camada de acesso ao modelo" (o que o livro chama de model API / gateway).

O que ele oferece:
    cliente               -> cliente compatível com a OpenAI, apontando para o OpenRouter
    MODELO, MODELO_FORTE  -> modelo barato/rápido e modelo mais forte (para comparar e para "juiz")
    MODELO_EMBEDDING      -> modelo de embeddings
    perguntar(prompt)     -> manda um prompt e devolve só o texto
    conversar(mensagens)  -> chamada completa (devolve o objeto inteiro: choices, usage, logprobs...)
    perguntar_json(...)   -> resposta em JSON já convertida para dict
    embeddings(textos)    -> matriz de vetores (uma linha por texto)
    similaridade(a, b)    -> similaridade de cosseno
    contar_tokens(texto)  -> quantos tokens o texto tem
    gasto()               -> quanto você gastou nesta sessão

Modo simulado (IA_FAKE=1): nada sai da máquina e não há custo. As respostas são falsas, mas têm o mesmo
formato das reais (inclusive logprobs, várias amostras, streaming, JSON e chamadas de ferramentas).
Serve para testar o código. O gabarito é testado assim.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import hashlib
import json
import os
import re
import time
from pathlib import Path
from types import SimpleNamespace as NS

import numpy as np

__all__ = ["cliente", "MODELO", "MODELO_FORTE", "MODELO_EMBEDDING", "perguntar", "conversar", "perguntar_json",
           "embeddings", "contar_tokens", "gasto", "similaridade", "FAKE"]

MODELO = "openai/gpt-4o-mini"          # barato e rápido
MODELO_FORTE = "openai/gpt-4o"         # mais caro: comparação e juiz
MODELO_EMBEDDING = "openai/text-embedding-3-small"
FAKE = os.environ.get("IA_FAKE") == "1"

_ARQ_CHAVE = Path.home() / ".secrets" / "openrouter.dpapi"
_gasto = {"usd": 0.0, "chamadas": 0, "tokens_in": 0, "tokens_out": 0}


def _ler_chave() -> str:
    """Chave do OpenRouter: variável OPENROUTER_API_KEY ou o arquivo cifrado com DPAPI."""
    if os.environ.get("OPENROUTER_API_KEY"):
        return os.environ["OPENROUTER_API_KEY"]
    if not _ARQ_CHAVE.exists():
        raise RuntimeError("Chave do OpenRouter não encontrada. Rode no PowerShell:\n"
                           "  & \"$HOME\\.claude\\skills\\jev\\set-key.ps1\"")
    blob = bytes.fromhex(_ARQ_CHAVE.read_text(encoding="ascii").strip())

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wt.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    entrada = DATA_BLOB(len(blob), ctypes.cast(ctypes.create_string_buffer(blob, len(blob)), ctypes.POINTER(ctypes.c_char)))
    saida = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(entrada), None, None, None, None, 0, ctypes.byref(saida)):
        raise RuntimeError("Não consegui decifrar a chave (ela só abre no seu usuário do Windows).")
    try:
        return ctypes.string_at(saida.pbData, saida.cbData).decode("utf-16-le")
    finally:
        ctypes.windll.kernel32.LocalFree(saida.pbData)


# ============================================================ modo simulado
_JSON_PADRAO = {"resposta": "resposta simulada", "rotulo": "duvida", "categoria": "duvida", "intencao": "duvida",
                "sentimento": "neutro", "nota": 4, "pontuacao": 4, "vencedor": "A", "motivo": "simulado",
                "seguro": True, "relevante": True, "acao": "responder", "prioridade": "media",
                "itens": ["item simulado"], "perguntas": ["pergunta simulada?"], "resumo": "resumo simulado"}


def _conteudo(m):
    c = m.get("content") if isinstance(m, dict) else getattr(m, "content", "")
    if isinstance(c, list):
        c = " ".join(p.get("text", "") for p in c if isinstance(p, dict))
    return c or ""


def _papel(m):
    return m.get("role") if isinstance(m, dict) else getattr(m, "role", "")


def _instancia(schema: dict, chave: str = ""):
    """Gera um valor que obedece a um JSON Schema simples."""
    if "enum" in schema:
        return schema["enum"][0]
    if "anyOf" in schema:
        return _instancia(schema["anyOf"][0], chave)
    t = schema.get("type", "string")
    if isinstance(t, list):
        t = [x for x in t if x != "null"][0]
    if t == "object":
        return {k: _instancia(v, k) for k, v in schema.get("properties", {}).items()}
    if t == "array":
        return [_instancia(schema.get("items", {"type": "string"}), chave)]
    if t == "integer":
        return max(int(schema.get("minimum", 4)), min(int(schema.get("maximum", 4)), 4))
    if t == "number":
        return 0.8
    if t == "boolean":
        return True
    padrao = _JSON_PADRAO.get(chave)
    return padrao if isinstance(padrao, str) else f"{chave or 'texto'} simulado"


def _resposta_falsa(texto_total: str, pedido: str, opcoes: dict, indice: int) -> str:
    rf = opcoes.get("response_format")
    if isinstance(rf, dict) and rf.get("type") == "json_schema":
        return json.dumps(_instancia(rf["json_schema"]["schema"]), ensure_ascii=False)
    if (isinstance(rf, dict) and rf.get("type") == "json_object") or "json" in texto_total.lower():
        d = dict(_JSON_PADRAO)
        d["consulta"] = pedido[:80]
        return json.dumps(d, ensure_ascii=False)
    sufixo = f" (amostra {indice + 1})" if indice else ""
    return f"Resposta simulada{sufixo}: {pedido[:120]}"


def _tokens_falsos(texto: str) -> list[str]:
    return re.findall(r"\s*\S+", texto) or [texto]


def _logprobs_falsos(conteudo: str, top: int):
    itens = []
    for tok in _tokens_falsos(conteudo):
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        lp = -0.05 - 0.6 * ((h % 7) / 7)
        alternativas = [NS(token=tok, logprob=lp, bytes=None)] + [
            NS(token=f" alt{j}", logprob=lp - 1.5 * j, bytes=None) for j in range(1, max(top, 1))]
        itens.append(NS(token=tok, logprob=lp, bytes=None, top_logprobs=alternativas[:top]))
    return NS(content=itens)


def _uso(entrada: str, saida: str):
    tin, tout = max(1, len(entrada) // 4), max(1, len(saida) // 4)
    return NS(prompt_tokens=tin, completion_tokens=tout, total_tokens=tin + tout, cost=0.0, model_extra={})


class _ChatFalso:
    def create(self, model, messages, stream=False, n=1, tools=None, logprobs=False, top_logprobs=0, **opcoes):
        texto = "\n".join(_conteudo(m) for m in messages)
        pedido = next((_conteudo(m) for m in reversed(messages) if _papel(m) == "user"), texto)
        papel_ultimo = _papel(messages[-1]) if messages else ""
        escolhas = []
        for i in range(n or 1):
            if tools and papel_ultimo != "tool":
                func = tools[0]["function"]
                props = func.get("parameters", {}).get("properties", {})
                args = {k: (pedido[:60] if v.get("type", "string") == "string" else 1) for k, v in props.items()}
                chamada = NS(id=f"call_{i}", type="function",
                             function=NS(name=func["name"], arguments=json.dumps(args, ensure_ascii=False)))
                msg = NS(role="assistant", content=None, tool_calls=[chamada])
                escolhas.append(NS(index=i, message=msg, finish_reason="tool_calls", logprobs=None))
                continue
            conteudo = _resposta_falsa(texto, pedido, opcoes, i)
            lp = _logprobs_falsos(conteudo, top_logprobs or 1) if logprobs else None
            escolhas.append(NS(index=i, message=NS(role="assistant", content=conteudo, tool_calls=None),
                               finish_reason="stop", logprobs=lp))
        if stream:
            return self._fluxo(escolhas[0].message.content or "", texto)
        saida = " ".join(c.message.content or "" for c in escolhas)
        return NS(id="falso", model=model, choices=escolhas, usage=_uso(texto, saida))

    @staticmethod
    def _fluxo(conteudo: str, entrada: str):
        time.sleep(0.05)
        for tok in _tokens_falsos(conteudo):
            time.sleep(0.005)
            yield NS(choices=[NS(index=0, delta=NS(content=tok, role="assistant"), finish_reason=None)], usage=None)
        yield NS(choices=[], usage=_uso(entrada, conteudo))


def _vetor_falso(texto: str, dim: int = 256) -> list[float]:
    v = np.zeros(dim)
    for palavra in re.findall(r"\w+", texto.lower()):
        h = int(hashlib.md5(palavra.encode()).hexdigest(), 16)
        v[h % dim] += 1.0 if (h >> 8) % 2 else -1.0
    v[0] += 0.5   # evita vetor nulo
    return list(v / np.linalg.norm(v))


class _EmbeddingsFalso:
    def create(self, model, input, **_):
        textos = [input] if isinstance(input, str) else input
        return NS(data=[NS(embedding=_vetor_falso(t), index=i) for i, t in enumerate(textos)],
                  usage=NS(prompt_tokens=sum(len(t) // 4 for t in textos), completion_tokens=0,
                           cost=0.0, model_extra={}))


class _ClienteFalso:
    def __init__(self):
        self.chat = NS(completions=_ChatFalso())
        self.embeddings = _EmbeddingsFalso()


# ============================================================ cliente real ou simulado
if FAKE:
    cliente = _ClienteFalso()
else:
    from openai import OpenAI
    cliente = OpenAI(base_url=os.environ.get("IA_BASE_URL", "https://openrouter.ai/api/v1"),
                     api_key=_ler_chave(), timeout=90)


def _registrar(uso) -> None:
    if uso is None:
        return
    _gasto["chamadas"] += 1
    _gasto["tokens_in"] += getattr(uso, "prompt_tokens", 0) or 0
    _gasto["tokens_out"] += getattr(uso, "completion_tokens", 0) or 0
    custo = getattr(uso, "cost", None)
    if custo is None and isinstance(getattr(uso, "model_extra", None), dict):
        custo = uso.model_extra.get("cost")
    _gasto["usd"] += float(custo or 0)


def conversar(mensagens: list[dict], modelo: str = MODELO, **opcoes):
    """Chamada completa. opcoes: temperature, top_p, max_tokens, n, logprobs, top_logprobs,
    response_format, tools, stream, seed..."""
    resposta = cliente.chat.completions.create(model=modelo, messages=mensagens, **opcoes)
    if not opcoes.get("stream"):
        _registrar(resposta.usage)
    return resposta


def perguntar(prompt: str, sistema: str | None = None, modelo: str = MODELO, **opcoes) -> str:
    """Manda um prompt e devolve só o texto da resposta."""
    mensagens = ([{"role": "system", "content": sistema}] if sistema else []) + [{"role": "user", "content": prompt}]
    return conversar(mensagens, modelo=modelo, **opcoes).choices[0].message.content


def perguntar_json(prompt: str, sistema: str | None = None, modelo: str = MODELO, **opcoes) -> dict:
    """Pede a resposta em JSON (modo json_object) e devolve um dict."""
    sistema = ((sistema or "") + "\nResponda somente com um objeto JSON válido.").strip()
    texto = perguntar(prompt, sistema=sistema, modelo=modelo, response_format={"type": "json_object"}, **opcoes)
    return json.loads(texto)


def embeddings(textos: list[str] | str, modelo: str = MODELO_EMBEDDING) -> np.ndarray:
    """Vetores dos textos (uma linha por texto)."""
    if isinstance(textos, str):
        textos = [textos]
    resposta = cliente.embeddings.create(model=modelo, input=textos)
    _registrar(getattr(resposta, "usage", None))
    return np.array([item.embedding for item in resposta.data])


def similaridade(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Similaridade de cosseno (1 = mesma direção, 0 = sem relação)."""
    a, b = np.atleast_2d(a), np.atleast_2d(b)
    a = a / np.linalg.norm(a, axis=-1, keepdims=True)
    b = b / np.linalg.norm(b, axis=-1, keepdims=True)
    return a @ b.T


def contar_tokens(texto: str, codificacao: str = "o200k_base") -> int:
    """Quantos tokens o texto tem (tokenizador dos modelos GPT-4o)."""
    import tiktoken
    return len(tiktoken.get_encoding(codificacao).encode(texto))


def gasto() -> str:
    """Resumo do que foi gasto nesta sessão do caderno."""
    g = _gasto
    modo = " (modo simulado)" if FAKE else ""
    return (f"{g['chamadas']} chamadas · {g['tokens_in']} tokens de entrada · "
            f"{g['tokens_out']} de saída · US$ {g['usd']:.5f}{modo}")
