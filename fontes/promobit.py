from datetime import datetime

import requests

URL = "https://api.promobit.com.br/offers"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def _data(s):
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z")
    except (TypeError, ValueError):
        return None


def buscar_ofertas(paginas: int = 2):
    """Retorna as ofertas mais recentes do Promobit (50 por página)."""
    ofertas, after = [], None
    for _ in range(paginas):
        params = {"after": after} if after else {}
        r = requests.get(URL, params=params, headers=HEADERS, timeout=20)
        r.raise_for_status()
        dados = r.json()
        for o in dados.get("offers", []):
            if o.get("offer_status_name") != "APPROVED":
                continue
            foto = o.get("offer_photo") or ""
            ofertas.append({
                "id": f"promobit:{o['offer_id']}",
                "titulo": o.get("offer_title", "").strip(),
                "preco": o.get("offer_price"),
                "preco_antigo": o.get("offer_old_price"),
                "tipo_preco": o.get("offer_price_type"),
                "desconto": o.get("offer_discont_percentage") or 0,
                "cupom": o.get("offer_coupon"),
                "loja": o.get("store_name"),
                "categoria_id": o.get("category_id"),
                "imagem": f"https://i.promobit.com.br{foto}" if foto.startswith("/") else foto or None,
                "link": f"https://www.promobit.com.br/oferta/{o['offer_slug']}/",
                "likes": o.get("offer_likes"),
                "publicado": _data(o.get("offer_published")),
            })
        after = dados.get("after")
        if not after:
            break
    return ofertas
