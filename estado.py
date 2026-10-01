import json
import time
from pathlib import Path

import ia
from qualidade import comparar

LIMITE = 5000  # quantos IDs guardar por categoria


class Estado:
    """Guarda o que já foi enviado para não repetir ofertas."""

    def __init__(self, caminho: Path):
        self.caminho = caminho
        self.dados = json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists() else {}

    def ja_viu(self, chave: str, item_id: str) -> bool:
        return item_id in self.dados.get(chave, [])

    def marcar(self, chave: str, item_id: str):
        lista = self.dados.setdefault(chave, [])
        if item_id not in lista:
            lista.append(item_id)
            del lista[:-LIMITE]

    def produto_recente(self, titulo: str, preco, dias: float):
        """Título do produto igual enviado nos últimos `dias` (ou esperando análise), ou None."""
        limite = time.time() - dias * 86400
        recentes = [p for p in self.dados.get("produtos_recentes", []) if p[1] >= limite]
        self.dados["produtos_recentes"] = recentes
        # Formato: [titulo, ts, preco]. Registros antigos só têm [palavras, ts].
        candidatos = [(p[0], p[2] if len(p) > 2 else None) for p in recentes]
        candidatos += [(r["oferta"]["titulo"], r["oferta"]["preco"]) for r in self.dados.get("revisao", {}).values()]
        talvez = []
        for outro, outro_preco in candidatos:
            resultado = comparar(titulo, outro, preco, outro_preco)
            if resultado == "igual":
                return outro
            if resultado == "talvez":
                talvez.append(outro)
        # Casos duvidosos: a IA desempata (no máximo 3 perguntas, das mais recentes)
        return next((outro for outro in reversed(talvez[-3:]) if ia.mesmo_produto(titulo, outro)), None)

    def registrar_produto(self, titulo: str, preco=None):
        self.dados.setdefault("produtos_recentes", []).append([titulo, time.time(), preco])

    def inicializado(self, chave: str) -> bool:
        return chave in self.dados

    def salvar(self):
        tmp = self.caminho.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.dados, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.caminho)
