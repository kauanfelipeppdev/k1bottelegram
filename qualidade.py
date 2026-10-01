"""Filtro de qualidade: decide se uma oferta (já classificada) merece ir pro grupo."""
import re
import time
from collections import defaultdict, deque
from datetime import datetime, timezone

import config
from classificador import normalizar


def motivo_para_descartar(o: dict):
    """Retorna o motivo do descarte, ou None se a oferta é boa."""
    if o.get("publicado"):
        idade_h = (datetime.now(timezone.utc) - o["publicado"]).total_seconds() / 3600
        if idade_h > config.MAX_IDADE_HORAS:
            return f"antiga ({idade_h:.0f}h)"
    if o.get("preco") is not None and o["preco"] < config.PRECO_MINIMO:
        return f"preço suspeito (R$ {o['preco']})"
    if (o.get("likes") or 0) < 0:
        return "avaliação negativa"
    if o.get("desconto") and o["desconto"] < config.DESCONTO_MINIMO:
        return f"desconto baixo ({o['desconto']:.0f}%)"
    return None


def palavras(titulo: str) -> list:
    return sorted(set(re.findall(r"[a-z0-9]{2,}", normalizar(titulo))))


def parecidos(a, b) -> bool:
    a, b = set(a), set(b)
    if not a or not b:
        return False
    return len(a & b) / len(a | b) >= 0.6


class Limite:
    """No máximo N envios por hora em cada tópico."""

    def __init__(self, por_hora: int):
        self.por_hora = por_hora
        self.envios = defaultdict(deque)

    def pode(self, topico: str) -> bool:
        fila, agora = self.envios[topico], time.time()
        while fila and agora - fila[0] > 3600:
            fila.popleft()
        return len(fila) < self.por_hora

    def registrar(self, topico: str):
        self.envios[topico].append(time.time())
