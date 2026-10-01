# bitdeofertask1 — bot de ofertas gamer (@k1ofertasbot)

Publica no Telegram:
- **Hardware** (placa de vídeo, processador, SSD, RAM, placa-mãe, fonte, gabinete, cooler, PC gamer)
- **Periféricos** (mouse, teclado, headset, monitor, mousepad, controle, webcam, microfone, cadeira)
- **Jogos grátis** (Epic Games e Steam com 100% OFF)

Fontes: API do Promobit (ofertas, a cada 5 min) e as APIs da Epic e da Steam (jogos, a cada 60 min).

## Configuração

1. `pip install -r requirements.txt`
2. Adicione o bot como **administrador** em cada canal ou grupo (com permissão para postar).
3. Mande uma mensagem em cada canal/tópico e rode `python bot.py --descobrir` para ver os IDs.
4. Preencha os `*_CHAT_ID` (e `*_THREAD_ID`, se for um grupo com tópicos) no `.env`.

## Uso

```
python bot.py --simular   # mostra no terminal o que seria enviado
python bot.py             # roda o bot
```

Na primeira execução as ofertas que já existem são só registradas, para não lotar o canal.
Depois disso, só as novas são enviadas. O que já foi enviado fica em `estado.json`.
Os termos de cada categoria ficam em `classificador.py`.
