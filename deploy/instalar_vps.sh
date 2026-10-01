#!/usr/bin/env bash
# Instala o bot como serviço systemd numa VPS Ubuntu/Debian.
# Uso (na VPS, dentro da pasta do projeto): sudo bash deploy/instalar_vps.sh
set -euo pipefail

DESTINO=/opt/k1ofertas
USUARIO=k1bot
ORIGEM="$(cd "$(dirname "$0")/.." && pwd)"

apt-get update -y
apt-get install -y python3 python3-venv rsync

id -u "$USUARIO" >/dev/null 2>&1 || useradd --system --home "$DESTINO" --shell /usr/sbin/nologin "$USUARIO"

mkdir -p "$DESTINO/data"
rsync -a --exclude '.git' --exclude '__pycache__' --exclude '*.log' --exclude 'data' \
      --exclude 'estado.json' --exclude 'marca' "$ORIGEM/" "$DESTINO/"

# Se você trouxe o estado.json do PC, ele vai para a pasta de dados (evita reenviar ofertas antigas).
if [ -f "$ORIGEM/estado.json" ] && [ ! -f "$DESTINO/data/estado.json" ]; then
  cp "$ORIGEM/estado.json" "$DESTINO/data/estado.json"
fi

if [ ! -f "$DESTINO/.env" ]; then
  echo "ERRO: crie $DESTINO/.env (copie do .env.example e preencha) e rode de novo." >&2
  exit 1
fi
chmod 600 "$DESTINO/.env"

python3 -m venv "$DESTINO/.venv"
"$DESTINO/.venv/bin/pip" install --upgrade pip -q
"$DESTINO/.venv/bin/pip" install -r "$DESTINO/requirements.txt" -q

chown -R "$USUARIO:$USUARIO" "$DESTINO"

cp "$DESTINO/deploy/k1ofertas.service" /etc/systemd/system/k1ofertas.service
systemctl daemon-reload
systemctl enable --now k1ofertas
systemctl --no-pager status k1ofertas
