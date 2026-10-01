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

## Análise de ofertas suspeitas

Ofertas com preço abaixo de `PRECO_MINIMO` ou avaliação negativa não são descartadas:
vão para o chat de `REVISAO_CHAT_ID` com os botões **✅ Postar** e **❌ Descartar**.
As aprovadas saem no grupo com o selo "✅ Analisada pela equipe K1". Se ninguém
decidir em `REVISAO_HORAS` (padrão 2h), a oferta expira.

Para receber no seu privado: mande `/start` para o bot, rode `python bot.py --descobrir`
(com o bot parado) e copie o `CHAT_ID` do tipo `private` para `REVISAO_CHAT_ID`.
