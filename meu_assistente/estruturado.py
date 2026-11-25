"""Transforma o texto de um chamado em dados validados."""
from typing import Literal

from pydantic import BaseModel, ValidationError

from ia import conversar

SISTEMA = ("Você classifica chamados de clientes da Nimbus. Categorias: cobranca (pagamento, fatura), "
          "acesso (login, senha, convite), bug (algo quebrado), duvida (copmo usar), cancelamento (encerrar conta).")


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
