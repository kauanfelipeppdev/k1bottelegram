"""Decide se uma oferta é de hardware, periférico ou nenhum dos dois.

A regra é: o termo que aparece PRIMEIRO no título vence. Títulos de oferta
normalmente começam pelo produto ("Mouse Gamer Logitech...", "Placa de Vídeo
RTX 4060..."), então isso resolve casos como "PC Gamer Ryzen 5 + Monitor".

O mesmo vale para os termos de exclusão: "Cabo HDMI para monitor" é descartado
(o produto é o cabo), mas "Mouse com cabo USB-C" passa (o produto é o mouse).
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
    r"\bheadphone\b", r"mouse ?pad", r"\bdeskpad\b", r"\bmonitor\b", r"\bwebcam\b",
    r"\bmicrofone\b", r"cadeira gamer", r"\bvolante\b", r"\bgamepad\b",
    r"\bjoystick\b", r"\bcontrole\b(?!.*remoto)", r"\bdualsense\b", r"\bdualshock\b",
    r"\bstream ?deck\b", r"\bcaptura\b.*\bvideo\b", r"\bplaca de captura\b",
]

# Itens de setup (vão para o tópico de periféricos).
SETUP = [
    r"\bsuporte\b.{0,25}\b(mesa|monitor|monitores|articulado|headset|fone|notebook|"
    r"controle|controles|placa de video|gpu|microfone|teclado|gabinete|pc|cpu)\b",
    r"\bsuporte (de|para) (mesa|parede)\b", r"\bbraco articulado\b",
    r"\bmesa gamer\b", r"\bescrivaninha gamer\b", r"\bmesa (para|de) (computador|escritorio)\b",
    r"\bapoio (de|para) (pulso|punho|pes)\b", r"\bhub usb\b", r"\bdock(ing)? station\b",
    r"\bbase (refrigerada|cooler)\b", r"\bcooler (para|de) notebook\b",
    r"\blight ?bar\b", r"\bfita de led\b.*\b(rgb|gamer|setup)\b",
]

# Se um desses termos vier ANTES do produto, o anúncio é do acessório/cupom: descarta.
EXCLUIR = [
    r"\bcupom\b", r"\bcupons\b", r"controle remoto",
    r"^\W*console\b", r"\bsuporte\b", r"\bsplitter\b", r"\bswitch hdmi\b",
    r"\bcapa\b", r"\bpelicula\b", r"\bcabo\b", r"\badaptador\b",
]

# Descartam a oferta em qualquer posição.
EXCLUIR_SEMPRE = [r"\btodo o site\b"]

# Categorias do Promobit que podem ter itens gamer.
# 1 = Informática, 3 = Eletrônicos, 4 = Games, None = sem categoria.
# Fora delas, só passa se o título deixar claro que é gamer/setup.
CATEGORIAS_ACEITAS = {1, 3, 4, None}

_HW = [re.compile(p) for p in HARDWARE]
_PF = [re.compile(p) for p in PERIFERICOS]
_ST = [re.compile(p) for p in SETUP]
_EX = [re.compile(p) for p in EXCLUIR]
_EX_SEMPRE = [re.compile(p) for p in EXCLUIR_SEMPRE]
_GAMER = re.compile(r"\bgam(er|ing)\b")


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.lower()


def _primeira_posicao(padroes, texto):
    posicoes = [m.start() for p in padroes if (m := p.search(texto))]
    return min(posicoes) if posicoes else None


def explicar(titulo: str, categoria_id=None):
    """Retorna (tipo, motivo). tipo é 'hardware', 'perifericos' ou None; motivo explica o descarte."""
    t = normalizar(titulo)
    if any(p.search(t) for p in _EX_SEMPRE):
        return None, "cupom/loja inteira"
    candidatos = [(pos, tipo) for pos, tipo in ((_primeira_posicao(_HW, t), "hardware"),
                                                (_primeira_posicao(_ST, t), "perifericos"),
                                                (_primeira_posicao(_PF, t), "perifericos"))
                  if pos is not None]
    if not candidatos:
        return None, "não é hardware/periférico"
    pos, tipo = min(candidatos)  # empate na posição: hardware vence
    ex = _primeira_posicao(_EX, t)
    if ex is not None and ex < pos:
        return None, "acessório/cupom (termo excluído antes do produto)"
    setup = _primeira_posicao(_ST, t) is not None
    if categoria_id not in CATEGORIAS_ACEITAS and not setup and not _GAMER.search(t):
        return None, f"categoria {categoria_id} fora das aceitas"
    return tipo, None


def classificar(titulo: str, categoria_id=None):
    """Retorna 'hardware', 'perifericos' ou None."""
    return explicar(titulo, categoria_id)[0]
