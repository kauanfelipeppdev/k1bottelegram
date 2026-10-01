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
