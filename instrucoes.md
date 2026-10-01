# Deploy do bot K1 Ofertas (@k1ofertasbot)

Este guia coloca o bot rodando 24h num servidor. O bot é um processo Python que fica
em loop (não é site e não precisa de porta aberta). Ele só precisa de:

- **Python 3.10+** (o Docker usa 3.13)
- **Acesso à internet** (Telegram, Promobit, Epic, Steam)
- **Uma pasta que não se apague** para o `estado.json`. É nele que fica o que já foi enviado.
  Se ele se perder, o bot faz a "primeira leitura" de novo (não reenvia nada, mas
  esquece quais produtos já postou nos últimos dias).

> ⚠️ **Rode só UMA cópia do bot.** Com duas cópias (ex.: o PC e o servidor) cada
> oferta sai duplicada. Feche o `iniciar.bat` no PC antes de ligar o servidor.

---

## 1. Estrutura do projeto

```
bitdeofertask1/
├── bot.py               # ponto de entrada (loop principal)
├── config.py            # lê o .env e as variáveis de ambiente
├── afiliados.py         # troca links pelos seus links de afiliado
├── classificador.py     # hardware / periféricos / descarta
├── qualidade.py         # filtro de qualidade e limite por hora
├── estado.py            # salva o que já foi enviado
├── telegram_api.py      # chamadas à API do Telegram
├── fontes/              # Promobit, canais do Telegram, Epic, Steam
├── requirements.txt
├── .env.example         # modelo de configuração (o .env real NUNCA vai pro git)
│
├── Dockerfile           # opção A: Docker
├── docker-compose.yml
├── .dockerignore
├── deploy/
│   ├── instalar_vps.sh      # opção B: instala como serviço systemd
│   └── k1ofertas.service
│
├── iniciar.bat          # só para rodar no Windows (PC local)
└── marca/               # logo (não vai para o servidor)
```

Arquivos que **não** vão para o servidor nem para o git: `.env`, `estado.json`,
`bot.log`, `__pycache__/`, `data/` (já estão no `.gitignore` e `.dockerignore`).

### Variável nova: `DATA_DIR`

Define a pasta onde ficam o `estado.json` e o `bot.log`. Se não for definida,
usa a pasta do projeto (como antes, no PC). No Docker ela é `/data` e no
serviço systemd é `/opt/k1ofertas/data`.

---

## 2. Antes de tudo (no seu PC)

1. **Teste localmente** que está tudo certo:
   ```
   python bot.py --simular
   ```
2. **Pare o bot local** (feche a janela do `iniciar.bat`).
3. **Guarde o `estado.json` e o `.env`** — você vai copiar os dois para o servidor.
   O `estado.json` evita que o bot recomece do zero.
4. **Crie um repositório git só do projeto.** Hoje o git está na sua pasta de
   usuário inteira (`C:\Users\Kauan Pereira`), o que não serve para deploy.
   Dentro da pasta do projeto:
   ```
   git init
   git add .
   git status          # confira: .env e estado.json NÃO podem aparecer
   git commit -m "Bot K1 Ofertas"
   ```
   Depois crie um repositório **privado** no GitHub e envie:
   ```
   git remote add origin https://github.com/SEU_USUARIO/bitdeofertask1.git
   git branch -M main
   git push -u origin main
   ```

---

## 3. Onde hospedar

| Opção | Custo | Quando escolher |
|---|---|---|
| **VPS** (Oracle Cloud Free, Hetzner, Contabo, DigitalOcean, Magalu Cloud...) | grátis a ~R$ 25/mês | Recomendado. Controle total, estado em disco. |
| **Railway / Fly.io / Render** com Docker | ~US$ 5/mês | Se não quiser administrar servidor. Precisa de **volume persistente**. |
| PC ligado 24h | luz | Já funciona com o `iniciar.bat`. |

> Serviços "free" que dormem por inatividade (Render free, Replit) **não servem**:
> o bot precisa ficar acordado o tempo todo.

---

## 4. Opção A — VPS com Docker (recomendado)

### 4.1 Instalar o Docker (Ubuntu/Debian)
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER   # saia e entre de novo no SSH depois disso
```

### 4.2 Baixar o projeto
```bash
git clone https://github.com/SEU_USUARIO/bitdeofertask1.git
cd bitdeofertask1
```

### 4.3 Enviar `.env` e `estado.json` do PC para o servidor
No **PowerShell do seu PC**, dentro da pasta do projeto:
```powershell
scp .env usuario@IP_DO_SERVIDOR:~/bitdeofertask1/.env
ssh usuario@IP_DO_SERVIDOR "mkdir -p ~/bitdeofertask1/data"
scp estado.json usuario@IP_DO_SERVIDOR:~/bitdeofertask1/data/estado.json
```
(Ou crie o `.env` no servidor com `cp .env.example .env && nano .env`.)

No servidor, proteja o arquivo:
```bash
chmod 600 .env
```

### 4.4 Subir o bot
```bash
docker compose up -d --build
docker compose logs -f          # Ctrl+C sai dos logs, o bot continua
```
Deve aparecer `Bot @k1ofertasbot iniciado.`

### 4.5 Comandos do dia a dia
```bash
docker compose ps                         # está rodando?
docker compose logs --tail 100            # últimas linhas do log
docker compose restart                    # reiniciar (ex.: depois de mudar o .env)
docker compose down                       # parar
docker compose run --rm bot python bot.py --simular     # simular sem enviar
docker compose run --rm bot python bot.py --descobrir   # ver IDs de chats/tópicos
```

### 4.6 Atualizar o código
No PC: `git add . && git commit -m "..." && git push`. No servidor:
```bash
cd ~/bitdeofertask1
git pull
docker compose up -d --build
```
O `estado.json` fica em `./data` e **não** é apagado no rebuild.

---

## 5. Opção B — VPS sem Docker (systemd)

1. Instale o git e baixe o projeto:
   ```bash
   sudo apt-get install -y git
   git clone https://github.com/SEU_USUARIO/bitdeofertask1.git
   cd bitdeofertask1
   ```
2. Coloque o `.env` e o `estado.json` **dentro dessa pasta** (via `scp`, como no 4.3,
   mas sem o `data/`).
3. Rode o instalador:
   ```bash
   sudo bash deploy/instalar_vps.sh
   ```
   O script cria o usuário `k1bot`, copia o projeto para `/opt/k1ofertas`, cria o
   ambiente virtual, move o `estado.json` para `/opt/k1ofertas/data/` e liga o serviço
   (ele também reinicia sozinho se cair ou se o servidor reiniciar).

4. Comandos úteis:
   ```bash
   sudo systemctl status k1ofertas
   sudo journalctl -u k1ofertas -f          # log ao vivo
   sudo systemctl restart k1ofertas         # depois de mudar o .env
   sudo systemctl stop k1ofertas
   ```

5. Atualizar o código:
   ```bash
   cd ~/bitdeofertask1 && git pull
   sudo bash deploy/instalar_vps.sh         # recopia e reinicia (mantém data/ e .env)
   ```

---

## 6. Opção C — Railway (sem servidor)

1. Em [railway.app](https://railway.app): **New Project → Deploy from GitHub repo** e
   escolha o repositório. Ele detecta o `Dockerfile` sozinho.
2. Em **Variables**, cole o conteúdo do seu `.env` (botão *Raw Editor*).
3. Em **Settings → Volumes**, crie um volume montado em **`/data`**.
   Sem o volume, o estado se perde a cada deploy.
4. Faça o deploy e acompanhe em **Deployments → View logs**.

O `estado.json` antigo não é copiado aqui: o bot faz a primeira leitura (só registra,
não envia) e segue normal a partir daí.

---

## 7. Checklist final

- [ ] Bot local parado (só uma cópia rodando)
- [ ] `.env` preenchido no servidor (token, `*_CHAT_ID`, `*_THREAD_ID`, afiliados)
- [ ] `estado.json` copiado para a pasta de dados (opcional, mas recomendado)
- [ ] Log mostra `Bot @k1ofertasbot iniciado.` e `ofertas: N novas enviadas.`
- [ ] Nenhum `ERROR` repetido no log
- [ ] Reiniciar o servidor (`sudo reboot`) e confirmar que o bot volta sozinho

## 8. Problemas comuns

| Sintoma | Causa / solução |
|---|---|
| `Defina TELEGRAM_TOKEN no arquivo .env` | `.env` não está no lugar certo ou a variável está vazia. |
| `chat not found` / `not enough rights` | O bot não é admin do canal/grupo, ou o `CHAT_ID` está errado. Rode `--descobrir`. |
| Ofertas duplicadas | Duas cópias rodando, ou o `estado.json` foi perdido (faltou volume). |
| Horário do Top 5 errado | O bot já usa horário de Brasília internamente; confira `TOP_DIA_HORA` no `.env`. |
| `403` / bloqueio no Promobit ou Steam | Alguns IPs de datacenter são bloqueados. Teste com `--simular`; se acontecer, troque de provedor. |

## 9. Segurança

- Nunca faça commit do `.env`. Se o token vazar, gere outro no **@BotFather** (`/revoke`).
- Deixe o repositório do GitHub **privado**, por garantia.
