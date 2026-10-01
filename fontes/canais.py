"""Lê ofertas de canais PÚBLICOS do Telegram pela página t.me/s/<canal> (sem login)."""
import html
import re
from datetime import datetime

import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

_MENSAGEM = re.compile(r'<div class="tgme_widget_message_wrap')
_POST = re.compile(r'data-post="[^"/]+/(\d+)"')
_TEXTO = re.compile(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', re.S)
_LINK = re.compile(r'href="(https?://[^"]+)"')
_PRECO = re.compile(r"R\$\s*([\d.]+(?:,\d{1,2})?)")
_CUPOM = re.compile(r"cupom\s*:\s*(.+)", re.I)
_DATA = re.compile(r'<time[^>]*datetime="([^"]+)"')
_FOTO = re.compile(r"tgme_widget_message_photo_wrap[^>]*?background-image:url\('([^']+)'\)")
# Linhas que não são nome de produto (avisos, links, preço)
_NAO_TITULO = re.compile(r"^(http|valor|cupom|link|r\$|apenas pelo|so no app|só no app|\(anuncio\))", re.I)

LOJAS = {
    "amazon": "Amazon", "amzn.to": "Amazon", "meli.la": "Mercado Livre",
    "mercadolivre": "Mercado Livre", "aliexpress": "AliExpress", "shopee": "Shopee",
    "kabum": "KaBuM!", "pichau": "Pichau", "terabyteshop": "Terabyte", "magazineluiza": "Magalu",
    "magalu": "Magalu",
}


def _loja(url: str):
    for chave, nome in LOJAS.items():
        if chave in url:
            return nome
    return None


def _preco(texto: str):
    m = _PRECO.search(texto)
    if not m:
        return None
    valor = m[1].replace(".", "").replace(",", ".")
    try:
        return float(valor)
    except ValueError:
        return None


def _titulo(linhas):
    for linha in linhas:
        limpa = re.sub(r"^[^\wÀ-ÿ]+", "", linha).strip()  # tira emojis do começo
        if len(limpa) >= 6 and not _NAO_TITULO.match(limpa):
            return limpa
    return None


def buscar_ofertas(canal: str):
    r = requests.get(f"https://t.me/s/{canal}", headers=HEADERS, timeout=20)
    r.raise_for_status()
    ofertas = []
    for bloco in _MENSAGEM.split(r.text)[1:]:
        post, corpo = _POST.search(bloco), _TEXTO.search(bloco)
        if not post or not corpo:
            continue
        links = [l for l in _LINK.findall(corpo[1]) if "t.me/" not in l]
        if not links:
            continue
        texto = html.unescape(re.sub(r"<[^>]+>", "", re.sub(r"<br\s*/?>", "\n", corpo[1])))
        linhas = [l.strip() for l in texto.splitlines() if l.strip()]
        titulo = _titulo(linhas)
        if not titulo:
            continue
        cupom = next((m[1].strip() for l in linhas if (m := _CUPOM.search(l))), None)
        data, foto = _DATA.search(bloco), _FOTO.search(bloco)
        ofertas.append({
            "id": f"tg:{canal}:{post[1]}",
            "fonte": "telegram",
            "titulo": titulo,
            "preco": _preco(texto),
            "preco_antigo": None,
            "tipo_preco": None,
            "desconto": 0,
            "cupom": cupom,
            "loja": _loja(links[0]),
            "categoria_id": None,
            # Foto do post (é a do produto). Link de loja encurtado quase nunca gera prévia com foto.
            "imagem": foto[1] if foto else None,
            "link": links[0],
            "publicado": datetime.fromisoformat(data[1]) if data else None,
        })
    return ofertas  # já vem da mais antiga para a mais nova
