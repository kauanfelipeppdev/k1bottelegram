"""Troca o link do Promobit pelo link direto da loja, com o SEU código de afiliado quando possível.

Lojas sem afiliado configurado recebem o link direto da loja (sem passar pelo site do
Promobit). Se algo der errado com o afiliado (código não configurado, produto não
identificado com segurança), mantém o link direto da loja.
"""
import hashlib
import hmac
import json
import logging
import re
import time
from urllib.parse import parse_qs, urlencode, urlsplit

import requests

import config
from classificador import normalizar

log = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
REDIRECT = "https://www.promobit.com.br/Redirect/to/{}/"

_AMAZON = re.compile(r"https?://(?:www\.)?amazon\.com\.br/[^'\"\s]*?/?(?:dp|gp/product)/([A-Z0-9]{10})")
_MELI = re.compile(r"https?://(?:meli\.la/[A-Za-z0-9]+|[^'\"\s]*mercadoli(?:vre|bre)\.com[^'\"\s]*)")
_ML_PRODUTO = re.compile(r'"product_id":"(MLB\d+)"[^{}]*?"url":"([^"]+)"')
_ML_TITULO = re.compile(r'<meta property="og:title" content="([^"]+)"')
_ALI_LINK = re.compile(r"https?://[\w.-]*aliexpress\.[a-z.]+/[^'\"\s<>]*")
_ALI_ITEM = re.compile(r"(?:/item/|/i/|productIds?=)(\d{6,})")
ALI_API = "https://api-sg.aliexpress.com/sync"
# Na página de redirecionamento do Promobit, o link da loja fica numa variável JavaScript
_LINK_PROMOBIT = re.compile(r"\bl = '([^']+)'")


def _desembrulhar(url: str) -> str:
    """Links de rede de afiliados (Rakuten, Awin) carregam o link da loja num parâmetro."""
    params = parse_qs(urlsplit(url).query)
    for chave in ("murl", "ued"):
        if params.get(chave):
            return params[chave][0]
    return url


def _loja_promobit(oferta_id: str):
    """Link direto da loja de uma oferta do Promobit, ou None se não achar."""
    for tentativa in range(3):
        r = requests.get(REDIRECT.format(oferta_id), headers=HEADERS, timeout=20)
        if r.status_code != 429:  # 429 = muitos acessos seguidos: espera e tenta de novo
            break
        espera = r.headers.get("Retry-After", "")
        time.sleep(min(int(espera), 60) if espera.isdigit() else 10)
    r.raise_for_status()
    m = _LINK_PROMOBIT.search(r.text)
    if not m or "promobit.com.br" in m[1]:
        return None
    return _desembrulhar(m[1])


def _palavras(texto: str) -> set:
    return {p for p in re.findall(r"[a-z0-9]+", normalizar(texto)) if len(p) > 1}


def _parecido(a: str, b: str) -> bool:
    pa, pb = _palavras(a), _palavras(b)
    if not pa or not pb:
        return False
    return len(pa & pb) / min(len(pa), len(pb)) >= 0.5


def _amazon(origem: str):
    m = _AMAZON.search(origem)
    if not m:
        return None
    if not config.AMAZON_TAG:  # sem tag: link limpo, sem o código de afiliado de terceiros
        return f"https://www.amazon.com.br/dp/{m[1]}"
    return f"https://www.amazon.com.br/dp/{m[1]}?{urlencode({'tag': config.AMAZON_TAG})}"


def _mercado_livre(link_ml: str, titulo: str):
    destino = requests.get(link_ml, headers=HEADERS, timeout=20)
    produto = _ML_PRODUTO.search(destino.text)
    titulo_ml = _ML_TITULO.search(destino.text)
    if not produto:
        return None
    url = json.loads(f'"{produto[2]}"')
    # Links de cupom/listas caem numa vitrine com um produto qualquer; confere o título.
    if not titulo_ml or not _parecido(titulo, titulo_ml[1]):
        log.info("ML: produto não confere (%r x %r), mantendo link original",
                 titulo, titulo_ml[1] if titulo_ml else None)
        return None
    url = "https://" + url.split("://")[-1]
    return f"{url}?{urlencode({'matt_word': config.ML_MATT_WORD, 'matt_tool': config.ML_MATT_TOOL})}"


def _ali_api(metodo: str, **params) -> dict:
    """Chamada assinada (HMAC-SHA256) à AliExpress Open Platform."""
    params.update(method=metodo, app_key=config.ALI_APP_KEY, sign_method="sha256",
                  timestamp=str(int(time.time() * 1000)))
    base = "".join(f"{k}{v}" for k, v in sorted(params.items()))
    params["sign"] = hmac.new(config.ALI_APP_SECRET.encode(), base.encode(),
                              hashlib.sha256).hexdigest().upper()
    r = requests.post(ALI_API, data=params, timeout=20)
    r.raise_for_status()
    return r.json()


def _aliexpress(origem: str):
    m = _ALI_LINK.search(origem)
    if not m:
        return None
    url = m[0]
    item = _ALI_ITEM.search(url)
    if not item:  # link encurtado (s.click, a.aliexpress.com/_xxx): segue o redirecionamento
        item = _ALI_ITEM.search(requests.get(url, headers=HEADERS, timeout=20).url)
    if not item:
        log.info("AliExpress: produto não identificado em %s, mantendo link original", url)
        return None
    dados = _ali_api("aliexpress.affiliate.link.generate", promotion_link_type="0",
                     source_values=f"https://pt.aliexpress.com/item/{item[1]}.html",
                     tracking_id=config.ALI_TRACKING_ID)
    resp = dados.get("aliexpress_affiliate_link_generate_response", {}).get("resp_result") or {}
    links = ((resp.get("result") or {}).get("promotion_links") or {}).get("promotion_link") or []
    if resp.get("resp_code") != 200 or not links or not links[0].get("promotion_link"):
        log.warning("AliExpress: API não gerou link para %s: %s", item[1], dados)
        return None
    return links[0]["promotion_link"]


def _link_da_loja(oferta: dict):
    """Link original da loja: do próprio canal, ou da página de redirecionamento do Promobit."""
    if oferta.get("fonte") == "telegram":
        return oferta["link"]
    return _loja_promobit(oferta["id"].split(":", 1)[1])


def link_afiliado(oferta: dict) -> str:
    loja = normalizar(oferta.get("loja") or "")
    try:
        origem = _link_da_loja(oferta)
    except Exception as e:
        log.warning("Não consegui o link da loja para %s: %s", oferta["id"], e)
        origem = None
    if not origem:
        return oferta["link"]
    try:
        if "amazon" in loja:
            if oferta.get("fonte") == "telegram":  # link encurtado (link.amazon, amzn.to)
                origem = requests.get(origem, headers=HEADERS, timeout=20).url
            return _amazon(origem) or origem
        if "mercado livre" in loja and config.ML_MATT_TOOL:
            m = _MELI.search(origem)
            return (_mercado_livre(m[0], oferta["titulo"]) if m else None) or origem
        if "aliexpress" in loja and config.ALI_APP_KEY:
            return _aliexpress(origem) or origem
    except Exception as e:
        log.warning("Falha ao gerar link de afiliado para %s: %s", oferta["id"], e)
    return origem
