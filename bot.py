"""Bot de ofertas gamer para Telegram.

Uso:
  python bot.py              roda o bot em loop
  python bot.py --descobrir  mostra os IDs de chats/tópicos onde o bot está
  python bot.py --simular    busca as ofertas e mostra no terminal, sem enviar
"""
import html
import logging
import sys
import time
from datetime import datetime, timezone, timedelta

import config
from afiliados import link_afiliado
from classificador import classificar
from estado import Estado
from qualidade import Limite, motivo_para_descartar
from fontes import canais, epic, promobit, steam
from telegram_api import Telegram

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                    handlers=[logging.StreamHandler(), logging.FileHandler(config.DADOS / "bot.log", encoding="utf-8")])
log = logging.getLogger("bot")

BRT = timezone(timedelta(hours=-3))
EMOJI = {"hardware": "🖥️", "perifericos": "🎮"}
NOME = {"hardware": "HARDWARE", "perifericos": "PERIFÉRICOS"}
limite = Limite(config.MAX_POR_HORA)


def _real(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _rodape():
    if not config.GRUPO_LINK:
        return []
    return ["", f"📲 Mais ofertas: <a href=\"{html.escape(config.GRUPO_LINK)}\">entre no K1 Ofertas</a>"]


def _pontuacao(o):
    """Quanto maior, melhor a oferta (usado no Top 5 do dia)."""
    return (o.get("desconto") or 0) + min(max(o.get("likes") or 0, 0), 20) * 2


def formatar_top(ofertas, dia):
    e = html.escape
    medalhas = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    linhas = [f"🏆 <b>TOP {len(ofertas)} OFERTAS DO DIA</b> · {dia:%d/%m}", ""]
    for medalha, o in zip(medalhas, ofertas):
        preco = f" — <b>{_real(o['preco'])}</b>" if o.get("preco") else ""
        desconto = f" (-{o['desconto']:.0f}%)" if o.get("desconto") else ""
        linhas.append(f"{medalha} {EMOJI[o['tipo']]} <a href=\"{e(o['link'])}\">{e(o['titulo'][:70])}</a>{preco}{desconto}")
    linhas += ["", "Encaminhe pra galera que tá montando o setup! 🎮"] + _rodape()
    return "\n".join(linhas)


def ciclo_top_do_dia(tg, estado):
    agora = datetime.now(BRT)
    hoje = agora.strftime("%Y-%m-%d")
    if agora.hour < config.TOP_DIA_HORA or estado.dados.get("ultimo_top") == hoje:
        return
    inicio = agora.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    do_dia = [o for o in estado.dados.get("enviadas", []) if o["ts"] >= inicio]
    estado.dados["ultimo_top"] = hoje
    if len(do_dia) < 3:
        log.info("Top do dia: poucas ofertas hoje (%d), pulando.", len(do_dia))
        return
    # Os 5 melhores, sem deixar um tópico dominar (máx. 3 de cada).
    escolhidas, por_tipo = [], {}
    for o in sorted(do_dia, key=_pontuacao, reverse=True):
        if por_tipo.get(o["tipo"], 0) < 3:
            escolhidas.append(o)
            por_tipo[o["tipo"]] = por_tipo.get(o["tipo"], 0) + 1
        if len(escolhidas) == 5:
            break
    geral = {"chat_id": config.DESTINOS["hardware"]["chat_id"], "thread_id": None}
    tg._chamar("sendMessage", chat_id=geral["chat_id"], text=formatar_top(escolhidas, agora),
               parse_mode="HTML", link_preview_options={"is_disabled": True})
    log.info("Top do dia enviado com %d ofertas.", len(escolhidas))


def _registrar_enviada(estado, o, tipo, link):
    enviadas = estado.dados.setdefault("enviadas", [])
    enviadas.append({"titulo": o["titulo"], "preco": o["preco"], "desconto": o.get("desconto") or 0,
                     "likes": o.get("likes") or 0, "tipo": tipo, "link": link, "ts": time.time()})
    del enviadas[:-300]


def formatar_oferta(o, tipo, link=None):
    e = html.escape
    linhas = [f"{EMOJI[tipo]} <b>{NOME[tipo]}</b>", "", f"<b>{e(o['titulo'])}</b>", ""]
    if o["preco"]:
        prefixo = "A partir de " if o["tipo_preco"] == "STARTING_AT" else ""
        preco = f"💰 {prefixo}<b>{_real(o['preco'])}</b>"
        if o["preco_antigo"] and o["preco_antigo"] > o["preco"]:
            preco += f"  <s>{_real(o['preco_antigo'])}</s>"
        if o["desconto"]:
            preco += f"  (-{o['desconto']:.0f}%)"
        linhas.append(preco)
    if o["cupom"]:
        linhas.append(f"🎟️ Cupom: <code>{e(o['cupom'])}</code>")
    if o["loja"]:
        linhas.append(f"🏬 {e(o['loja'])}")
    link = link or o["link"]
    texto_link = "Ver oferta" if "promobit.com.br" in link else f"Comprar na {e(o['loja'] or 'loja')}"
    linhas += ["", f"🔗 <a href=\"{e(link)}\">{texto_link}</a>"] + _rodape()
    return "\n".join(linhas)


def formatar_jogo(j):
    e = html.escape
    linhas = ["🆓 <b>JOGO GRÁTIS</b>", "", f"<b>{e(j['titulo'])}</b>", f"🕹️ {j['plataforma']}"]
    if j.get("preco_original"):
        linhas.append(f"💸 De <s>{e(j['preco_original'])}</s> por <b>R$ 0,00</b>")
    if j.get("ate"):
        linhas.append(f"⏰ Grátis até {j['ate'].astimezone(BRT):%d/%m às %H:%M}")
    linhas += ["", f"🔗 <a href=\"{e(j['link'])}\">Resgatar</a>"] + _rodape()
    return "\n".join(linhas)


def _processar(tg, estado, ofertas, chave, simular=False):
    """Envia as ofertas novas de uma fonte. Na primeira leitura só registra, para não lotar o grupo."""
    primeira_vez = not estado.inicializado(chave)
    if not simular:
        estado.dados.setdefault(chave, [])
    enviadas = 0
    for o in ofertas:
        tipo = classificar(o["titulo"], o["categoria_id"])
        if simular:
            if tipo:
                motivo = motivo_para_descartar(o)
                status = f"DESCARTE: {motivo}" if motivo else "ok"
                print(f"[{tipo}] {o['titulo'][:60]} — {o['preco']} ({o['loja']}) → {status}")
            continue
        if estado.ja_viu(chave, o["id"]):
            continue
        destino = config.DESTINOS.get(tipo) if tipo else None
        if tipo and destino and not primeira_vez:
            motivo = motivo_para_descartar(o)
            if not motivo and estado.produto_recente(o["titulo"], config.DIAS_SEM_REPETIR):
                motivo = "produto repetido"
            if motivo:
                log.info("Descartada (%s): %s", motivo, o["titulo"])
            elif not limite.pode(tipo):
                continue  # tópico no limite da hora: tenta de novo no próximo ciclo
            else:
                try:
                    link = link_afiliado(o)
                    tg.enviar(destino, formatar_oferta(o, tipo, link), o["imagem"])
                    limite.registrar(tipo)
                    _registrar_enviada(estado, o, tipo, link)
                    estado.registrar_produto(o["titulo"])
                    enviadas += 1
                    time.sleep(3)
                except Exception as e:
                    log.error("Erro ao enviar oferta %s: %s", o["id"], e)
                    continue
        elif tipo and not destino and not primeira_vez:
            continue  # destino ainda não configurado: tenta de novo quando for
        estado.marcar(chave, o["id"])
    if simular:
        return
    if primeira_vez:
        log.info("%s: primeira leitura, %d ofertas antigas registradas sem enviar.", chave, len(ofertas))
    else:
        log.info("%s: %d novas enviadas.", chave, enviadas)


def ciclo_ofertas(tg, estado, simular=False):
    # A API do Promobit vem da mais nova para a mais antiga; enviamos em ordem cronológica.
    _processar(tg, estado, list(reversed(promobit.buscar_ofertas())), "ofertas", simular)
    for canal in config.CANAIS_FONTE:
        try:
            _processar(tg, estado, canais.buscar_ofertas(canal), f"canal:{canal}", simular)
        except Exception as e:
            log.error("Erro lendo o canal %s: %s", canal, e)


def ciclo_jogos(tg, estado, simular=False):
    jogos = []
    for nome, fonte in (("Epic", epic), ("Steam", steam)):
        try:
            jogos += fonte.buscar_gratis()
        except Exception as e:
            log.error("Erro buscando jogos grátis na %s: %s", nome, e)
    destino = config.DESTINOS["jogos_gratis"]
    for j in jogos:
        if simular:
            print(f"[grátis] {j['plataforma']}: {j['titulo']} — {j['link']}")
            continue
        if estado.ja_viu("jogos", j["id"]) or not destino:
            continue
        try:
            tg.enviar(destino, formatar_jogo(j), j["imagem"])
            estado.marcar("jogos", j["id"])
            time.sleep(3)
        except Exception as e:
            log.error("Erro ao enviar jogo %s: %s", j["id"], e)
    if not simular:
        log.info("Jogos grátis encontrados: %d.", len(jogos))


def descobrir(tg):
    print(f"Bot: @{tg.eu()['username']}\n")
    vistos = set()
    for u in tg.atualizacoes():
        msg = u.get("message") or u.get("channel_post") or {}
        chat = msg.get("chat") or (u.get("my_chat_member") or {}).get("chat")
        if not chat:
            continue
        chave = (chat["id"], msg.get("message_thread_id"))
        if chave in vistos:
            continue
        vistos.add(chave)
        nome = chat.get("title") or chat.get("username") or chat.get("first_name")
        linha = f"{chat['type']:<10} CHAT_ID={chat['id']:<16} {nome}"
        if msg.get("is_topic_message"):
            linha += f"   (tópico THREAD_ID={msg['message_thread_id']})"
        print(linha)
    if not vistos:
        print("Nada encontrado. Adicione o bot como admin no canal/grupo, mande uma mensagem\n"
              "lá (em cada tópico, se usar tópicos) e rode este comando de novo.")


def main():
    if not config.TOKEN:
        sys.exit("Defina TELEGRAM_TOKEN no arquivo .env")
    tg = Telegram(config.TOKEN)

    if "--descobrir" in sys.argv:
        return descobrir(tg)

    estado = Estado(config.ARQUIVO_ESTADO)
    if "--simular" in sys.argv:
        ciclo_ofertas(tg, estado, simular=True)
        ciclo_jogos(tg, estado, simular=True)
        return

    faltando = [k for k, v in config.DESTINOS.items() if not v]
    if faltando:
        log.warning("Destinos sem configuração no .env (serão ignorados): %s", ", ".join(faltando))
    log.info("Bot @%s iniciado.", tg.eu()["username"])

    proximo_ofertas = proximo_jogos = 0.0
    while True:
        agora = time.time()
        if agora >= proximo_ofertas:
            try:
                ciclo_ofertas(tg, estado)
            except Exception as e:
                log.error("Erro no ciclo de ofertas: %s", e)
            estado.salvar()
            proximo_ofertas = agora + config.INTERVALO_OFERTAS
        if agora >= proximo_jogos:
            try:
                ciclo_jogos(tg, estado)
            except Exception as e:
                log.error("Erro no ciclo de jogos: %s", e)
            estado.salvar()
            proximo_jogos = agora + config.INTERVALO_JOGOS
        try:
            ciclo_top_do_dia(tg, estado)
        except Exception as e:
            log.error("Erro no Top do dia: %s", e)
        estado.salvar()
        time.sleep(15)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("Bot encerrado.")
