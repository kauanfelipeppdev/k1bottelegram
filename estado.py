import json
import time
from pathlib import Path

from qualidade import palavras, parecidos

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

    def produto_recente(self, titulo: str, dias: float) -> bool:
        """True se um produto parecido já foi enviado nos últimos `dias` (de qualquer fonte)."""
        limite = time.time() - dias * 86400
        recentes = [p for p in self.dados.get("produtos_recentes", []) if p[1] >= limite]
        self.dados["produtos_recentes"] = recentes
        alvo = palavras(titulo)
        return any(parecidos(alvo, p[0].split()) for p in recentes)

    def registrar_produto(self, titulo: str):
        self.dados.setdefault("produtos_recentes", []).append([" ".join(palavras(titulo)), time.time()])

    def inicializado(self, chave: str) -> bool:
        return chave in self.dados

    def salvar(self):
        tmp = self.caminho.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.dados, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.caminho)
