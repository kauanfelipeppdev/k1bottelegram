# Notebook velho como servidor do bot K1 Ofertas

Guia completo para deixar o bot rodando 24h num notebook antigo, do zero.
Siga **na ordem** e não pule etapas.

**Termos usados neste guia:**
- **PC** = seu computador principal, onde o projeto está hoje.
- **Note** = o notebook velho que vai virar servidor.

---

## Etapa 0 — Escolher o caminho

O bot é leve (uns 50 MB de RAM), mas o sistema operacional pode pesar.
Veja o que o note tem: no Windows, `Configurações → Sistema → Sobre`.
Anote a **RAM**, se o sistema é de **32 ou 64 bits** e **qual Windows** é.

| Situação do note | Caminho |
|---|---|
| Windows 10/11, 4 GB de RAM ou mais e você quer continuar usando o note no Windows | **Caminho A — Windows** |
| Até 4 GB de RAM, ou muito lento, ou HD mecânico, e você pode **apagar tudo** dele | **Caminho B — Linux** (recomendado) |
| Windows 7 / 8 / 8.1 | **Caminho B — Linux** (o bot precisa do Python 3.10+, que não roda nesses Windows) |
| Processador de 32 bits | **Caminho B, com Debian 32 bits** (ver B.1) |

> ⚠️ O **Caminho B apaga todo o conteúdo do note**. Salve antes o que for importante dele.

---

## Etapa 1 — Preparar o hardware (vale para os dois caminhos)

1. **Bateria:**
   - Se a bateria sai fácil (trava embaixo do note), **tire** e use o note só na tomada.
     Bateria velha carregando 24h pode **estufar** e é risco de incêndio.
   - Se não sai, deixe como está, mas olhe de vez em quando: se a carcaça ou o
     touchpad começarem a levantar, **desligue e tire da tomada na hora**.
   - Se tirar a bateria, saiba que qualquer piscada de luz desliga o note.
     A Etapa 1.4 ajuda nisso.
2. **Local:** coloque o note numa superfície **dura e plana** (mesa, nunca cama ou
   sofá), com as saídas de ar livres. Se ele esquenta muito, limpe a ventoinha
   (assistência técnica ou ar comprimido).
3. **Internet:** use **cabo de rede** ligado direto no roteador sempre que der.
   Wi-Fi funciona, mas cai mais.
4. **BIOS: ligar sozinho quando a luz voltar** (opcional, nem todo note tem):
   1. Desligue o note. Ligue e aperte várias vezes a tecla da BIOS assim que a tela
      acender (geralmente **F2**, **Del**, **F10** ou **Esc**, depende da marca).
   2. Procure algo como **"AC Power Recovery"**, **"Power On AC"**, **"Restore on AC
      Power Loss"** ou **"Wake on AC"** e coloque em **On / Power On**.
   3. Salve com **F10** e confirme.
   4. Se não encontrar, tudo bem: depois de uma queda de luz você só precisa ligar
      no botão.

---

## Etapa 2 — Preparar os arquivos no PC (vale para os dois caminhos)

1. **Pare o bot no PC:** feche a janela do `iniciar.bat`, ou aperte `Ctrl+C` nela.
   A partir de agora o bot só pode rodar no note. Duas cópias rodando = ofertas duplicadas.
2. Abra o **PowerShell** na pasta do projeto:
   - No Explorador de Arquivos, abra `C:\Users\Kauan Pereira\Documents\dev\bitdeofertask1`
   - Clique na barra de endereço, digite `powershell` e aperte Enter.
3. Crie um pacote com tudo que o note precisa, incluindo o `.env` e o `estado.json`:
   ```powershell
   tar -czf ..\k1ofertas.tar.gz --exclude=__pycache__ --exclude=*.log --exclude=marca .
   ```
   Vai aparecer o arquivo `k1ofertas.tar.gz` em `C:\Users\Kauan Pereira\Documents\dev\`.
4. Confira se o `.env` e o `estado.json` entraram:
   ```powershell
   tar -tzf ..\k1ofertas.tar.gz
   ```
   Na lista precisam aparecer `./.env` e `./estado.json`.

> 🔒 Esse pacote tem o **token do bot**. Não mande por WhatsApp, e-mail nem nuvem pública.
> Use pendrive ou rede local, como explicado abaixo. Depois de instalar, apague a cópia do pendrive.

---

# CAMINHO A — Note com Windows

### A.1 Instalar o Python
1. No note, abra https://www.python.org/downloads/ e baixe o **Python 3.13** (botão amarelo).
2. Abra o instalador e, **antes de clicar em Install**, marque a caixinha
   **"Add python.exe to PATH"** na parte de baixo. Esse passo é o mais importante.
3. Clique em **Install Now** e espere terminar. Se aparecer
   **"Disable path length limit"**, clique nele.
4. Para conferir, abra o **Prompt de Comando** (`Win+R` → `cmd` → Enter) e digite:
   ```
   python --version
   ```
   Tem que aparecer `Python 3.13.x`. Se der "não é reconhecido", reinstale marcando o PATH.

### A.2 Copiar o projeto para o note
1. Copie o `k1ofertas.tar.gz` para um pendrive e do pendrive para o note.
2. No note, crie a pasta `C:\k1ofertas`. Use um caminho curto, sem espaços e fora da
   Área de Trabalho.
3. Coloque o `k1ofertas.tar.gz` dentro de `C:\k1ofertas`.
4. Abra o Prompt de Comando e rode:
   ```
   cd C:\k1ofertas
   tar -xzf k1ofertas.tar.gz
   del k1ofertas.tar.gz
   ```
5. Confira se apareceram `bot.py`, `iniciar.bat`, `.env` e `estado.json` dentro de
   `C:\k1ofertas`. O `.env` é arquivo oculto: no Explorador, ative
   `Exibir → Mostrar → Itens ocultos`.

### A.3 Instalar a dependência e testar
No Prompt de Comando:
```
cd C:\k1ofertas
python -m pip install -r requirements.txt
python bot.py --simular
```
O teste deve listar ofertas como `[hardware] ...` e `[grátis] ...` **sem enviar nada**.
Se aparecer erro, veja a seção **Problemas** no final.

### A.4 Nunca dormir, nem com a tampa fechada
1. `Win+R` → digite `control powercfg.cpl` → Enter.
2. Na esquerda, clique em **"Escolher a função de fechar a tampa"**.
3. Em **"Ao fechar a tampa"**, escolha **"Nada a fazer"** nas duas colunas
   (Bateria e Conectado). Se não tiver bateria, só aparece uma coluna.
4. Faça o mesmo em **"Ao pressionar o botão de energia"** → **Desligar**.
5. Clique em **Salvar alterações**.
6. Abra o **Prompt de Comando como administrador** (menu Iniciar → digite `cmd` →
   botão direito → *Executar como administrador*) e rode:
   ```
   powercfg /change standby-timeout-ac 0
   powercfg /change hibernate-timeout-ac 0
   powercfg /change monitor-timeout-ac 1
   powercfg /change standby-timeout-dc 0
   powercfg /change hibernate-timeout-dc 0
   ```
   Assim o note nunca suspende, e a tela apaga em 1 minuto para economizar luz.

### A.5 Abrir o bot sozinho quando o Windows ligar
1. `Win+R` → digite `shell:startup` → Enter. Abre a pasta **Inicializar**.
2. Em outra janela, abra `C:\k1ofertas`, clique com o **botão direito** no
   `iniciar.bat` → **Mostrar mais opções** → **Criar atalho**.
3. **Arraste o atalho** criado para a pasta **Inicializar**.
4. (Opcional) Para a janela abrir minimizada: botão direito no atalho →
   **Propriedades** → **Executar: Minimizada** → OK.

### A.6 Login automático (sem ele, o bot não volta depois de uma queda de luz)
1. **Só no Windows 11:** `Configurações → Contas → Opções de entrada` e **desative**
   *"Para maior segurança, permitir apenas a entrada do Windows Hello..."*.
2. `Win+R` → digite `netplwiz` → Enter.
3. Desmarque **"Os usuários devem digitar um nome de usuário e uma senha para usar
   este computador"**.
   - Se essa opção não aparecer, faça o passo 1 e reinicie o note.
4. Clique em **OK**, digite a senha da conta duas vezes e confirme.
   Se a conta é Microsoft (e-mail), use a senha do e-mail, não o PIN.
5. Reinicie e confira que o Windows entra direto, sem pedir senha.

### A.7 Evitar reinícios surpresa do Windows Update
1. `Configurações → Windows Update → Opções avançadas → Horário ativo`.
2. Coloque **Manualmente**, das **8h às 2h** (o máximo permitido).
3. Ele ainda vai reiniciar às vezes, mas com A.5 e A.6 o bot volta sozinho.

### A.8 Ligar e testar de verdade
1. **Reinicie o note.**
2. Ele deve entrar direto no Windows e abrir a janela **"K1 Ofertas Bot"**.
3. Na janela deve aparecer `Bot @k1ofertasbot iniciado.` e, em seguida, linhas como
   `ofertas: 0 novas enviadas.`
4. Feche a tampa, espere 10 minutos, abra e confira que a janela continua rodando.
5. **Teste de queda:** tire o note da tomada (se tiver bateria, espere ela acabar ou
   desligue segurando o botão), ligue de novo e veja se o bot volta sozinho.

### A.9 Atualizar o bot depois (quando mudar o código no PC)
1. No note, feche a janela do bot.
2. No PC, refaça a **Etapa 2**, passos 2 e 3.
3. Copie o pacote novo para o note e extraia em `C:\k1ofertas` com o mesmo comando do A.2.
4. ⚠️ O pacote traz o `estado.json` do PC, que agora está **desatualizado**. Antes de
   extrair, faça uma cópia do `estado.json` do note e, depois de extrair, coloque essa
   cópia de volta. Outra opção: no PC, apague o `estado.json` do pacote antes de copiar.
5. Abra o `iniciar.bat` de novo, ou reinicie o note.

**Pronto, o Caminho A acabou.** Pule para **Manutenção** no final.

---

# CAMINHO B — Note com Linux (Ubuntu Server)

Você vai precisar de:
- um **pendrive de 4 GB ou mais**, que será **apagado**;
- o note ligado na tomada e, de preferência, no cabo de rede;
- o PC para preparar o pendrive e, depois, controlar o note.

### B.1 Baixar o sistema (no PC)
- **Note de 64 bits (quase todos depois de 2010):** baixe o **Ubuntu Server 24.04 LTS**
  em https://ubuntu.com/download/server → *Option 2: Manual server installation* →
  **Download**. O arquivo termina em `.iso` e tem uns 2,5 GB.
- **Note de 32 bits:** o Ubuntu não serve. Baixe o **Debian 12 "i386" netinst** em
  https://www.debian.org/distrib/netinst (seção *Small CDs* → **i386**).
  A instalação é parecida; as diferenças estão marcadas com **[Debian]** abaixo.

### B.2 Gravar o pendrive (no PC)
1. Baixe o **Rufus** em https://rufus.ie (versão "Portátil" serve).
2. Coloque o pendrive no PC e abra o Rufus.
3. **Dispositivo:** escolha o pendrive. ⚠️ Confira bem para não apagar outro disco.
4. **Seleção de boot:** clique em **SELECIONAR** e escolha o `.iso` baixado.
5. Deixe o resto como está e clique em **INICIAR**.
6. Se perguntar sobre "modo ISO" ou "DD", escolha **o recomendado (ISO)**.
   Confirme que o pendrive será apagado.
7. Espere aparecer **PRONTO** e feche o Rufus.

### B.3 Dar boot pelo pendrive (no note)
1. Com o note **desligado**, coloque o pendrive nele.
2. Ligue e aperte várias vezes a tecla do **menu de boot**:

   | Marca | Tecla |
   |---|---|
   | Dell | F12 |
   | HP | Esc, depois F9 |
   | Lenovo | F12 (ou o botãozinho "Novo" na lateral) |
   | Acer | F12 (se não funcionar, ative "F12 Boot Menu" na BIOS) |
   | Asus | Esc |
   | Samsung | F10 |
   | Positivo | F7 ou Esc |

3. Escolha o pendrive na lista (o nome dele, ou "USB", ou "UEFI: ...").
4. Se o note recusar com uma mensagem de *Secure Boot*: entre na BIOS (Etapa 1.4),
   **desative o Secure Boot**, salve e repita.
5. No menu preto que aparece, escolha **"Try or Install Ubuntu Server"** e aperte Enter.

### B.4 Instalar o Ubuntu Server
No instalador, use **setas**, **Tab**, **Espaço** (marcar) e **Enter** (confirmar).

1. **Language:** `English`. O instalador em inglês é o mais estável; o bot continua em português.
2. **Installer update available:** `Continue without updating`.
3. **Keyboard:** Layout `Portuguese (Brazil)`, Variant `Portuguese (Brazil)` → `Done`.
   Teste digitando `ç` no campo de teste, se houver.
4. **Type of installation:** deixe **Ubuntu Server** marcado (não o "minimized") → `Done`.
5. **Network:**
   - **Cabo:** deve aparecer a interface (ex.: `enp3s0`) com um IP tipo `192.168.x.x`.
     **Anote esse IP** e vá em `Done`.
   - **Wi-Fi:** selecione a interface que começa com `wl` (ex.: `wlp2s0`) → `Edit Wi-Fi` →
     escolha a rede, digite a senha → `Save`. Espere aparecer o IP e anote.
   - Se o Wi-Fi não aparecer, o note precisa de driver: use cabo durante a instalação
     e veja **B.7** depois.
6. **Proxy:** deixe vazio → `Done`.
7. **Ubuntu archive mirror:** espere o teste passar → `Done`.
8. **Storage configuration:** deixe **"Use an entire disk"** marcado e o disco do note
   selecionado. **Desmarque** "Set up this disk as an LVM group" (fica mais simples).
   → `Done`.
9. **Storage summary:** confira → `Done` → **`Continue`**.
   ⚠️ É aqui que o note é apagado.
10. **Profile setup:**
    - *Your name:* `Kauan`
    - *Your server's name:* `k1server`
    - *Pick a username:* `kauan`. Use letras minúsculas e **anote**.
    - *Choose a password:* uma senha forte. **Anote**, você vai usar sempre.
    → `Done`.
11. **Upgrade to Ubuntu Pro:** `Skip for now` → `Continue`.
12. **SSH Setup:** marque **[X] Install OpenSSH server** com Espaço. **Não pule isso**,
    é o que permite controlar o note pelo PC. Não importe chaves. → `Done`.
13. **Featured server snaps:** não marque nada → `Done`.
14. Espere instalar (10–40 min em note velho). Quando aparecer **`Reboot Now`**, selecione.
15. Se pedir *"Please remove the installation medium"*, **tire o pendrive** e aperte Enter.
16. Depois de reiniciar, a tela mostra muitas mensagens e para em `k1server login:`.
    Digite o usuário (`kauan`) e a senha. **A senha não aparece enquanto você digita, é normal.**

**[Debian]** Diferenças na instalação: escolha *Install* (não "Graphical install"),
idioma Português, teclado "Português Brasileiro". Em **senha do root**, deixe **em branco**
(assim seu usuário ganha `sudo`). Em *particionamento*, use "Assistido – usar o disco
inteiro" → "Todos os arquivos em uma partição". Na tela **"Seleção de software"**,
**desmarque** "Ambiente de trabalho Debian" e "GNOME", e **marque** só **"servidor SSH"**
e **"utilitários de sistema padrão"**. Instale o GRUB no disco principal (`/dev/sda`).

### B.5 Primeiros comandos (no note, logado)
Digite um por vez e aperte Enter. Quando pedir senha, é a sua senha.

1. Atualizar tudo (pode demorar):
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
2. Ajustar o fuso horário:
   ```bash
   sudo timedatectl set-timezone America/Sao_Paulo
   ```
3. Ver o IP do note:
   ```bash
   hostname -I
   ```
   **Anote o primeiro número** (ex.: `192.168.0.25`).

### B.6 Fechar a tampa sem desligar e nunca suspender
1. Abra o arquivo de configuração:
   ```bash
   sudo nano /etc/systemd/logind.conf
   ```
2. Use as setas para achar as linhas abaixo. Apague o `#` do começo e deixe assim:
   ```
   HandleLidSwitch=ignore
   HandleLidSwitchExternalPower=ignore
   HandleLidSwitchDocked=ignore
   ```
3. Salve: `Ctrl+O` → Enter → `Ctrl+X`.
4. Aplique e bloqueie a suspensão de vez:
   ```bash
   sudo systemctl restart systemd-logind
   sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
   ```
5. Feche a tampa, espere 1 minuto, abra e aperte Enter: tem que continuar ligado.

### B.7 (Só se usar Wi-Fi e ele não foi configurado na instalação)
1. Veja o nome da interface Wi-Fi:
   ```bash
   ip link
   ```
   É a que começa com `wl` (ex.: `wlp2s0`). Se não houver nenhuma, a placa precisa de
   driver proprietário. Nesse caso use cabo; é mais simples.
2. Crie a configuração:
   ```bash
   sudo nano /etc/netplan/99-wifi.yaml
   ```
3. Cole isto, trocando `wlp2s0`, `NOME_DA_REDE` e `SENHA` (os espaços importam, use
   espaços e não Tab):
   ```yaml
   network:
     version: 2
     wifis:
       wlp2s0:
         dhcp4: true
         access-points:
           "NOME_DA_REDE":
             password: "SENHA"
   ```
4. Salve (`Ctrl+O`, Enter, `Ctrl+X`) e aplique:
   ```bash
   sudo chmod 600 /etc/netplan/99-wifi.yaml
   sudo netplan apply
   hostname -I
   ```

### B.8 Fixar o IP do note
Se o IP mudar, o PC não acha mais o note. Escolha **uma** forma:
- **No roteador (melhor):** entre no painel do roteador (geralmente `192.168.0.1` ou
  `192.168.1.1`, com o usuário e a senha da etiqueta) e procure **"Reserva de DHCP"**,
  **"DHCP estático"** ou **"Address Reservation"**. Reserve o IP anotado para o `k1server`.
- **Pelo Tailscale (também resolve o acesso fora de casa):** veja **B.14**.

### B.9 Controlar o note pelo PC (SSH)
A partir daqui você pode deixar o note de lado, com a tampa fechada, e fazer tudo pelo PC.
1. No PC, abra o **PowerShell**.
2. Conecte, trocando pelo seu usuário e IP:
   ```powershell
   ssh kauan@192.168.0.25
   ```
3. Na primeira vez ele pergunta *"Are you sure you want to continue connecting"*:
   digite `yes` e Enter.
4. Digite a senha do note. Se aparecer `kauan@k1server:~$`, você está dentro do note.
5. Para sair, digite `exit`.

### B.10 Enviar o projeto para o note
1. No **PowerShell do PC** (fora do SSH), vá até a pasta onde está o pacote da Etapa 2:
   ```powershell
   cd "C:\Users\Kauan Pereira\Documents\dev"
   scp k1ofertas.tar.gz kauan@192.168.0.25:~
   ```
2. Entre no note e extraia:
   ```powershell
   ssh kauan@192.168.0.25
   ```
   ```bash
   mkdir -p ~/bitdeofertask1
   tar -xzf ~/k1ofertas.tar.gz -C ~/bitdeofertask1
   rm ~/k1ofertas.tar.gz
   cd ~/bitdeofertask1
   ls -a
   ```
   Têm que aparecer `bot.py`, `.env`, `estado.json` e a pasta `deploy`.
3. Corrija as quebras de linha que o Windows pode ter colocado (é seguro rodar sempre):
   ```bash
   sed -i 's/\r$//' deploy/instalar_vps.sh deploy/k1ofertas.service .env
   ```

### B.11 Instalar o bot como serviço
Ainda no note, dentro de `~/bitdeofertask1`:
```bash
sudo bash deploy/instalar_vps.sh
```
O script faz tudo sozinho:
- instala o Python e as ferramentas;
- cria o usuário de sistema `k1bot`, que roda o bot sem acesso de administrador;
- copia o projeto para `/opt/k1ofertas`;
- coloca o `estado.json` em `/opt/k1ofertas/data/`;
- protege o `.env` (`chmod 600`);
- cria o ambiente Python e instala o `requests`;
- liga o serviço `k1ofertas` e o deixa ligado para sempre (inclusive depois de reiniciar).

No final ele mostra o status. Procure **`Active: active (running)`** em verde.

### B.12 Ver se está funcionando
```bash
sudo journalctl -u k1ofertas -f
```
Deve aparecer `Bot @k1ofertasbot iniciado.` e, em seguida, `ofertas: N novas enviadas.`
Aperte `Ctrl+C` para sair do log. O bot **continua rodando**.

Teste extra (simular sem enviar):
```bash
cd /opt/k1ofertas
sudo -u k1bot DATA_DIR=/opt/k1ofertas/data .venv/bin/python bot.py --simular
```

### B.13 Teste de reinício e queda de luz
1. Reinicie o note:
   ```bash
   sudo reboot
   ```
2. Espere 2 minutos, conecte de novo pelo SSH e confira:
   ```bash
   systemctl status k1ofertas
   ```
   Tem que estar `active (running)` **sem você ter feito nada**.
3. Teste de queda: tire o note da tomada (sem bateria, ou desligue segurando o botão),
   ligue de novo e repita o passo 2.

### B.14 (Opcional) Acessar o note de fora de casa com o Tailscale
1. Crie uma conta grátis em https://tailscale.com (dá para entrar com Google).
2. No note:
   ```bash
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up
   ```
   Ele mostra um link. Abra no PC, faça login e aprove o note.
3. No PC, instale o Tailscale para Windows e entre na mesma conta.
4. No painel do Tailscale, o note aparece com um IP `100.x.x.x` fixo.
   Use `ssh kauan@100.x.x.x` de qualquer lugar.

### B.15 Atualizar o bot depois (quando mudar o código no PC)
1. No PC, refaça a **Etapa 2**, passos 2 e 3, e depois o **B.10** (o `scp` e a extração).
   O `.env` vem no pacote: se mudou alguma configuração no PC, ela vai junto.
2. No note:
   ```bash
   cd ~/bitdeofertask1
   sed -i 's/\r$//' deploy/instalar_vps.sh deploy/k1ofertas.service .env
   sudo bash deploy/instalar_vps.sh
   ```
   O `estado.json` do note **não é substituído**, porque o script só copia se ainda não
   existir. Assim o histórico de ofertas enviadas é mantido.
3. Confira com `sudo journalctl -u k1ofertas -f`.

**Mudar só uma configuração do `.env`, direto no note:**
```bash
sudo nano /opt/k1ofertas/.env
sudo systemctl restart k1ofertas
```

---

# Manutenção

### Comandos do dia a dia (Linux)
| O que fazer | Comando |
|---|---|
| Ver se está rodando | `systemctl status k1ofertas` |
| Log ao vivo | `sudo journalctl -u k1ofertas -f` |
| Últimas 100 linhas | `sudo journalctl -u k1ofertas -n 100` |
| Só os erros de hoje | `sudo journalctl -u k1ofertas --since today -p err` |
| Reiniciar o bot | `sudo systemctl restart k1ofertas` |
| Parar o bot | `sudo systemctl stop k1ofertas` |
| Ligar o bot | `sudo systemctl start k1ofertas` |
| Espaço em disco | `df -h /` |
| Memória | `free -h` |
| Temperatura | `sudo apt install -y lm-sensors && sensors` |
| Desligar o note com segurança | `sudo poweroff` |

### Backup do estado (uma vez por mês, no PC)
- **Linux:**
  ```powershell
  scp kauan@192.168.0.25:/opt/k1ofertas/data/estado.json "C:\Users\Kauan Pereira\Documents\dev\estado-backup.json"
  ```
  Se der "Permission denied", rode antes no note:
  `sudo chmod 644 /opt/k1ofertas/data/estado.json`.
- **Windows:** copie `C:\k1ofertas\estado.json` para um pendrive.

### Rotina sugerida
- **Toda semana:** dê uma olhada no log ou no canal para ver se as ofertas estão saindo.
- **Todo mês (Linux):** `sudo apt update && sudo apt upgrade -y && sudo reboot`.
  O Ubuntu já instala atualizações de segurança sozinho, mas esse comando completa o resto.
- **Sempre:** veja se a bateria não estufou e se a ventoinha não está barulhenta.

---

# Problemas

| Sintoma | Solução |
|---|---|
| `python` não é reconhecido (Windows) | Reinstale o Python marcando **"Add python.exe to PATH"** (A.1). |
| `No module named 'requests'` | Windows: `python -m pip install -r requirements.txt`. Linux: rode o `instalar_vps.sh` de novo. |
| `Defina TELEGRAM_TOKEN no arquivo .env` | O `.env` não foi copiado. Confira com `ls -a` (Linux) ou "Itens ocultos" (Windows). |
| `ERRO: crie /opt/k1ofertas/.env` no script | O `.env` não estava em `~/bitdeofertask1`. Refaça o B.10 e confira com `ls -a`. |
| `$'\r': command not found` no script | Faltou o comando `sed` do B.10, passo 3. |
| Ofertas saindo duplicadas | Tem outra cópia do bot rodando. Feche o `iniciar.bat` do PC. |
| `chat not found` / `not enough rights` | O bot não é admin do canal/grupo, ou o ID está errado. |
| `ssh: connect ... timed out` | O note está desligado, o IP mudou (veja o IP na tela dele com `hostname -I` e faça o B.8) ou o PC está em outra rede. |
| Note desliga ao fechar a tampa | Refaça o A.4 (Windows) ou o B.6 (Linux). |
| Note não liga sozinho depois de queda de luz | Normal se a BIOS não tem a opção da Etapa 1.4. Ligue no botão; o bot sobe sozinho. |
| Bot parou e o log não mostra nada | Linux: `sudo systemctl restart k1ofertas`. Windows: reinicie o note. |
| Muitos `Erro buscando...` seguidos | A internet do note caiu. Confira o cabo/Wi-Fi; o bot volta sozinho quando a rede volta. |
| Note muito quente ou desligando sozinho | Superaquecimento: limpe a ventoinha e deixe em superfície dura. |

---

# Checklist final

- [ ] Bateria retirada, ou verificada que não está estufada
- [ ] Note em superfície dura, de preferência no cabo de rede
- [ ] Bot do PC **fechado**
- [ ] `python bot.py --simular` funcionou no note
- [ ] Tampa fechada e o note continua ligado
- [ ] Note reiniciado e o bot voltou **sozinho**
- [ ] Log mostra `Bot @k1ofertasbot iniciado.` e sem `ERROR` repetido
- [ ] Uma oferta nova apareceu no canal
- [ ] (Linux) IP fixado no roteador ou Tailscale instalado
- [ ] Pacote `k1ofertas.tar.gz` apagado do pendrive
