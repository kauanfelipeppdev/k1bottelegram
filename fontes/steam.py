import html
import re

import requests

# Busca da loja: preço máximo "grátis" + só itens em promoção = jogos pagos com 100% OFF.
# category1=998 restringe a jogos (sem DLCs, trilhas sonoras etc.).
URL = "https://store.steampowered.com/search/results/"
PARAMS = {"maxprice": "free", "specials": "1", "category1": "998",
          "infinite": "1", "cc": "br", "l": "brazilian", "count": "50"}
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

_LINHA = re.compile(r'<a href="(?P<link>https://store\.steampowered\.com/app/(?P<appid>\d+)/[^"?]*)[^"]*"'
                    r'.*?<span class="title">(?P<titulo>[^<]+)</span>', re.S)
_PRECO_ORIGINAL = re.compile(r'discount_original_price">([^<]+)<')


def buscar_gratis():
    """Jogos pagos que estão de graça (100% OFF) na Steam agora."""
    r = requests.get(URL, params=PARAMS, headers=HEADERS, timeout=20)
    r.raise_for_status()
    corpo = r.json().get("results_html", "")
    jogos = []
    for bloco in corpo.split('<a href="')[1:]:
        m = _LINHA.search('<a href="' + bloco)
        if not m:
            continue
        preco = _PRECO_ORIGINAL.search(bloco)
        appid = m["appid"]
        jogos.append({
            "id": f"steam:{appid}",
            "titulo": html.unescape(m["titulo"]).strip(),
            "plataforma": "Steam",
            "ate": None,
            "imagem": f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg",
            "link": m["link"],
            "preco_original": html.unescape(preco[1]).strip() if preco else None,
        })
    return jogos


# Promoções: os mais vendidos da Steam que estão com desconto agora.
PARAMS_PROMO = {"specials": "1", "filter": "topsellers", "category1": "998",
                "infinite": "1", "cc": "br", "l": "brazilian", "count": "50"}
_DESCONTO = re.compile(r'data-discount="(\d+)"')
_PRECO_FINAL = re.compile(r'data-price-final="(\d+)"')
_AVALIACAO = re.compile(r'search_review_summary[^"]*" data-tooltip-html="([^"&]+)&lt;br&gt;(\d+)% [^\d]*([\d.,]+)')


def _reais(texto):
    return float(re.sub(r"[^\d,]", "", texto).replace(",", "."))


def buscar_promocoes():
    """Jogos mais vendidos da Steam que estão em promoção (pagos, com desconto)."""
    r = requests.get(URL, params=PARAMS_PROMO, headers=HEADERS, timeout=20)
    r.raise_for_status()
    corpo = r.json().get("results_html", "")
    jogos = []
    for bloco in corpo.split('<a href="')[1:]:
        m = _LINHA.search('<a href="' + bloco)
        desconto, final = _DESCONTO.search(bloco), _PRECO_FINAL.search(bloco)
        original = _PRECO_ORIGINAL.search(bloco)
        if not m or not desconto or not final or not original or int(final[1]) == 0:
            continue
        avaliacao = _AVALIACAO.search(bloco)
        appid = m["appid"]
        jogos.append({
            "id": f"steam:{appid}",
            "titulo": html.unescape(m["titulo"]).strip(),
            "plataforma": "Steam",
            "preco": int(final[1]) / 100,
            "preco_antigo": _reais(html.unescape(original[1])),
            "desconto": int(desconto[1]),
            "avaliacao": (f"{html.unescape(avaliacao[1])} ({avaliacao[2]}% de "
                          f"{avaliacao[3].replace(',', '.')} análises)") if avaliacao else None,
            "ate": None,
            "imagem": f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg",
            "link": m["link"],
        })
    return jogos
