import logging
import time

import requests

log = logging.getLogger(__name__)


class Telegram:
    def __init__(self, token: str):
        self.base = f"https://api.telegram.org/bot{token}"

    def _chamar(self, metodo: str, **dados):
        dados = {k: v for k, v in dados.items() if v is not None}
        for tentativa in range(3):
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

    def enviar(self, destino: dict, texto: str, imagem: str | None = None):
        comum = {"chat_id": destino["chat_id"], "message_thread_id": destino.get("thread_id"),
                 "parse_mode": "HTML"}
        if imagem:
            try:
                return self._chamar("sendPhoto", photo=imagem, caption=texto, **comum)
            except RuntimeError as e:
                log.warning("Falha ao enviar foto (%s), mandando só texto", e)
        # Sem foto própria: deixa o Telegram montar a prévia do link (foto da loja).
        preview = {"is_disabled": False, "prefer_large_media": True} if imagem is None else {"is_disabled": True}
        return self._chamar("sendMessage", text=texto, link_preview_options=preview, **comum)

    def atualizacoes(self):
        return self._chamar("getUpdates", allowed_updates=["message", "channel_post", "my_chat_member"])

    def eu(self):
        return self._chamar("getMe")
