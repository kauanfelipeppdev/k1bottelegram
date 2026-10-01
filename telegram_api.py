import json
import logging
import time

import requests

log = logging.getLogger(__name__)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


class Telegram:
    def __init__(self, token: str):
        self.base = f"https://api.telegram.org/bot{token}"

    def _chamar(self, metodo: str, arquivos=None, **dados):
        dados = {k: v for k, v in dados.items() if v is not None}
        if arquivos:  # upload (multipart): campos que não são texto vão como JSON
            dados = {k: v if isinstance(v, str) else json.dumps(v) for k, v in dados.items()}
        for tentativa in range(3):
            if arquivos:
                r = requests.post(f"{self.base}/{metodo}", data=dados, files=arquivos, timeout=60)
            else:
                r = requests.post(f"{self.base}/{metodo}", json=dados, timeout=30)
            resp = r.json()
            if resp.get("ok"):
                return resp["result"]
            espera = (resp.get("parameters") or {}).get("retry_after")
            if r.status_code == 429 and espera:
                log.warning("Limite do Telegram, aguardando %ss", espera)
                time.sleep(espera + 1)
                continue
            raise RuntimeError(f"{metodo}: {resp.get('description')}")
        raise RuntimeError(f"{metodo}: falhou após várias tentativas")

    def enviar(self, destino: dict, texto: str, imagem: str | None = None, botoes: dict | None = None):
        comum = {"chat_id": destino["chat_id"], "message_thread_id": destino.get("thread_id"),
                 "parse_mode": "HTML", "reply_markup": botoes}
        if imagem:
            try:
                return self._chamar("sendPhoto", photo=imagem, caption=texto, **comum)
            except RuntimeError as e:
                erro = e
            # O Telegram não consegue baixar algumas URLs (ex.: fotos de canais); baixamos e enviamos o arquivo.
            try:
                foto = requests.get(imagem, headers=HEADERS, timeout=20)
                foto.raise_for_status()
                return self._chamar("sendPhoto", arquivos={"photo": ("foto.jpg", foto.content)},
                                    caption=texto, **comum)
            except (RuntimeError, requests.RequestException) as e:
                log.warning("Falha ao enviar foto (%s / %s), mandando só texto", erro, e)
        # Sem foto (ou ela falhou): deixa o Telegram montar a prévia do link (foto da loja).
        preview = {"is_disabled": False, "prefer_large_media": True}
        return self._chamar("sendMessage", text=texto, link_preview_options=preview, **comum)

    def atualizacoes(self, offset=None, espera=0, tipos=("message", "channel_post", "my_chat_member")):
        return self._chamar("getUpdates", offset=offset, timeout=espera, allowed_updates=list(tipos))

    def eu(self):
        return self._chamar("getMe")
