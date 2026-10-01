from datetime import datetime, timezone

import requests

URL = "https://store-site-backend-static-ipv4.ak.epicgames.com/freeGamesPromotions"
PARAMS = {"locale": "pt-BR", "country": "BR", "allowCountries": "BR"}


def _data(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def _slug(jogo):
    for m in (jogo.get("catalogNs") or {}).get("mappings") or []:
        if m.get("pageSlug"):
            return m["pageSlug"]
    for m in jogo.get("offerMappings") or []:
        if m.get("pageSlug"):
            return m["pageSlug"]
    slug = jogo.get("productSlug") or jogo.get("urlSlug")
    return slug.split("/")[0] if slug else None


def _imagem(jogo):
    imagens = {i["type"]: i["url"] for i in jogo.get("keyImages", [])}
    for tipo in ("OfferImageWide", "DieselStoreFrontWide", "Thumbnail", "OfferImageTall"):
        if tipo in imagens:
            return imagens[tipo]
    return None


def buscar_gratis():
    """Jogos com 100% de desconto na Epic neste momento."""
    r = requests.get(URL, params=PARAMS, timeout=20)
    r.raise_for_status()
    elementos = r.json()["data"]["Catalog"]["searchStore"]["elements"]
    agora = datetime.now(timezone.utc)
    jogos = []
    for j in elementos:
        promos = (j.get("promotions") or {}).get("promotionalOffers") or []
        for bloco in promos:
            for oferta in bloco.get("promotionalOffers", []):
                ini, fim = _data(oferta.get("startDate")), _data(oferta.get("endDate"))
                gratis = oferta.get("discountSetting", {}).get("discountPercentage") == 0
                if gratis and ini and fim and ini <= agora <= fim:
                    slug = _slug(j)
                    jogos.append({
                        "id": f"epic:{j['id']}:{oferta.get('startDate')}",
                        "titulo": j["title"],
                        "plataforma": "Epic Games",
                        "ate": fim,
                        "imagem": _imagem(j),
                        "link": f"https://store.epicgames.com/pt-BR/p/{slug}" if slug
                                else "https://store.epicgames.com/pt-BR/free-games",
                        "preco_original": (j.get("price") or {}).get("totalPrice", {})
                                          .get("fmtPrice", {}).get("originalPrice"),
                    })
    return jogos
