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
    if o.get("desconto") and o["desconto"] < config.DESCONTO_MINIMO:
        return f"desconto baixo ({o['desconto']:.0f}%)"
    return None


def motivo_de_suspeita(o: dict):
    """Retorna por que a oferta é suspeita (vai para análise da equipe), ou None."""
    if o.get("preco") is not None and o["preco"] < config.PRECO_MINIMO:
        return f"preço suspeito (R$ {o['preco']})"
    if (o.get("likes") or 0) < 0:
        return "avaliação negativa"
    return None


def palavras(titulo: str) -> list:
    return sorted(set(re.findall(r"[a-z0-9]{2,}", normalizar(titulo))))


# Palavras que aparecem em todo tipo de anúncio e não dizem qual é o produto.
GENERICAS = set("""
de da do das dos para com sem em no na por ou e o a os as um uma the and for with
gamer gaming game games pc computador original originais novo nova lacrado oferta promocao
mouse teclado headset fone fones ouvido headphone monitor webcam microfone controle cadeira
mousepad mouse pad gabinete cooler water fonte memoria ram ssd hd hdd nvme placa video mae
processador notebook kit fio wireless bluetooth usb tipo type rgb argb led preto preta branco branca
pro max mini lite plus ultra edition esports sports music som audio espacial surround driver drivers
microfone reducao ruido cancelamento modos modo tela bateria base carregamento sensor switch switches
mecanico mecanica optico teclas hot swappable dpi hz mhz ghz gb tb mm cm polegadas pol
interno interna externo disco estado solido desktop laptop amd intel nvidia geforce radeon
""".split())

# Especificações técnicas: aparecem em produtos de marcas e modelos diferentes, então não
# servem para saber se dois anúncios são do mesmo produto (ex.: dois monitores 24" IPS 144Hz FHD).
_SPEC = re.compile(
    r"^(\d{1,2}|\d+(gb|tb|mb|mbs|gbps|mhz|ghz|khz|hz|w|mm|cm|dpi|mah|g|ms|k|kdpi|p|pol|v|x|fps|rpm|nm)"
    r"|\d{3,4}x\d{3,4}|hdr\d*|g?ddr\d+x?|pcie\d*|gen\d|m2|usb\d*|wifi\d*e?|bt\d*|cl\d+"
    r"|ips|va|tn|oled|qled|hd|fhd|qhd|uhd|wqhd|mbr|nativo|sync|freesync|gsync|hdmi|displayport|dp)$")


def _relevantes(titulo: str) -> set:
    return {p for p in palavras(titulo) if p not in GENERICAS and not _SPEC.match(p)}


def _codigos(relevantes: set) -> set:
    """Códigos de modelo: letra+número (g203, v9, 5700x, nk68) ou número de 3+ dígitos (4060)."""
    return {p for p in relevantes if
            (re.search(r"\d", p) and re.search(r"[a-z]", p)) or (p.isdigit() and len(p) >= 3)}


def comparar(titulo_a: str, titulo_b: str, preco_a=None, preco_b=None):
    """'igual' se é com certeza o mesmo produto, 'talvez' se vale perguntar à IA, senão None."""
    a, b = _relevantes(titulo_a), _relevantes(titulo_b)
    if not a or not b:
        return None
    ca, cb = _codigos(a), _codigos(b)
    if ca and cb and not ca & cb:
        return None  # modelos diferentes (ex.: G5 x G7, 4060 x 4070)
    comum = a & b
    # Cada um tem um código que o outro não tem (ex.: i5 12400F x i5 13400F): não dá pra ter certeza.
    codigo_diferente = bool(ca - cb) and bool(cb - ca)
    if not codigo_diferente and len(comum) >= 2 and len(comum) / min(len(a), len(b)) >= 0.6:
        return "igual"
    preco_perto = not (preco_a and preco_b) or abs(preco_a - preco_b) / max(preco_a, preco_b) <= 0.3
    if comum & (ca | cb) and preco_perto:
        return "talvez"
    return None


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
