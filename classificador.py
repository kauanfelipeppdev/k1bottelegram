"""Decide se uma oferta é de hardware, periférico ou nenhum dos dois.

A regra é: o termo que aparece PRIMEIRO no título vence. Títulos de oferta
normalmente começam pelo produto ("Mouse Gamer Logitech...", "Placa de Vídeo
RTX 4060..."), então isso resolve casos como "PC Gamer Ryzen 5 + Monitor".
"""
import re
import unicodedata

HARDWARE = [
    r"placa de video", r"placa grafica", r"geforce", r"\brtx\s?\d", r"\bgtx\s?\d",
    r"radeon", r"\brx\s?\d{3,4}", r"\barc\s?[ab]\d{3}",
    r"processador", r"\bryzen", r"\bcore i[3579]\b", r"\bcore ultra", r"\bi[3579][- ]\d{4,5}",
    r"\bssd\b", r"\bnvme\b", r"\bm\.2\b", r"\bhd externo\b", r"\bhdd\b", r"\bhd \d+ ?tb",
    r"memoria ram", r"\bddr[45]\b", r"\bplaca[- ]mae\b", r"motherboard",
    r"\bfonte\b.*\b(\d{3,4} ?w|atx|80 plus)", r"\bgabinete\b", r"water ?cooler",
    r"air ?cooler", r"\bcooler\b", r"pasta termica", r"kit upgrade",
    r"placa de rede", r"\bax2\d0\b", r"\bwi-?fi 6e?\b.*\bpci",
    r"\bpc gamer\b", r"notebook gamer", r"computador gamer",
]

PERIFERICOS = [
    r"\bmouse\b", r"\bteclado\b", r"\bheadset\b", r"\bfone\b.*\bgamer\b",
    r"\bheadphone gamer", r"mouse ?pad", r"\bmonitor\b", r"\bwebcam\b",
    r"\bmicrofone\b", r"cadeira gamer", r"\bvolante\b", r"\bgamepad\b",
    r"\bjoystick\b", r"\bcontrole\b(?!.*remoto)", r"\bdualsense\b", r"\bdualshock\b",
    r"\bstream ?deck\b", r"\bcaptura\b.*\bvideo\b", r"\bplaca de captura\b",
]

# Termos que, se aparecerem, descartam a oferta (cupons genéricos, etc.)
EXCLUIR = [
    r"\bcupom\b", r"\bcupons\b", r"\btodo o site\b", r"controle remoto",
    r"^\W*console\b", r"\bsuporte\b", r"\bsplitter\b", r"\bswitch hdmi\b",
    r"\bcapa\b", r"\bpelicula\b", r"\bcabo\b", r"\badaptador\b",
]

# Categorias do Promobit que podem ter itens gamer.
# 1 = Informática, 3 = Eletrônicos, 4 = Games, None = sem categoria.
CATEGORIAS_ACEITAS = {1, 3, 4, None}

_HW = [re.compile(p) for p in HARDWARE]
_PF = [re.compile(p) for p in PERIFERICOS]
_EX = [re.compile(p) for p in EXCLUIR]


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.lower()


def _primeira_posicao(padroes, texto):
    posicoes = [m.start() for p in padroes if (m := p.search(texto))]
    return min(posicoes) if posicoes else None


def classificar(titulo: str, categoria_id=None):
    """Retorna 'hardware', 'perifericos' ou None."""
    if categoria_id not in CATEGORIAS_ACEITAS:
        return None
    t = normalizar(titulo)
    if any(p.search(t) for p in _EX):
        return None
    hw = _primeira_posicao(_HW, t)
    pf = _primeira_posicao(_PF, t)
    if hw is None and pf is None:
        return None
    if pf is None or (hw is not None and hw <= pf):
        return "hardware"
    return "perifericos"
