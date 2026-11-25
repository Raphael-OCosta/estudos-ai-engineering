"""Núcleo do assistente da Nimbus: uma chamada ao modelo com medição."""
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
