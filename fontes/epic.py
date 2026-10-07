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


# Promoções: a lista "Mais vendidos" da loja, só o que está com desconto (e não grátis).
GRAPHQL = "https://store.epicgames.com/graphql"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
CONSULTA_PROMO = """
query maisVendidos($slug: String, $country: String!, $locale: String) {
  Storefront { collectionLayout(slug: $slug, locale: $locale) { collectionOffers {
    title id offerType productSlug urlSlug
    catalogNs { mappings(pageType: "productHome") { pageSlug } }
    offerMappings { pageSlug }
    keyImages { type url }
    price(country: $country) {
      totalPrice { discountPrice originalPrice }
      lineOffers { appliedRules { endDate } }
    }
  } } }
}"""


def buscar_promocoes():
    """Jogos mais vendidos da Epic que estão em promoção (pagos, com desconto)."""
    r = requests.post(GRAPHQL, headers=HEADERS, timeout=20, json={
        "query": CONSULTA_PROMO, "variables": {"slug": "top-sellers", "country": "BR", "locale": "pt-BR"}})
    r.raise_for_status()
    ofertas = ((r.json().get("data") or {}).get("Storefront") or {}).get("collectionLayout") or {}
    jogos = []
    for j in ofertas.get("collectionOffers") or []:
        preco = ((j.get("price") or {}).get("totalPrice") or {})
        final, original = preco.get("discountPrice") or 0, preco.get("originalPrice") or 0
        if j.get("offerType") != "BASE_GAME" or not final or final >= original:
            continue  # sem desconto, ou grátis (esses vão para o tópico de jogos grátis)
        regras = [regra for linha in j["price"].get("lineOffers") or [] for regra in linha.get("appliedRules") or []]
        slug = _slug(j)
        jogos.append({
            "id": f"epic:{j['id']}",
            "titulo": j["title"],
            "plataforma": "Epic Games",
            "preco": final / 100,
            "preco_antigo": original / 100,
            "desconto": round((1 - final / original) * 100),
            "avaliacao": None,
            "ate": _data(regras[0].get("endDate")) if regras else None,
            "imagem": _imagem(j),
            "link": f"https://store.epicgames.com/pt-BR/p/{slug}" if slug
                    else "https://store.epicgames.com/pt-BR/",
        })
    return jogos
