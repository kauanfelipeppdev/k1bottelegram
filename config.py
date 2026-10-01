import os
from pathlib import Path

BASE = Path(__file__).parent


def _carregar_env(caminho: Path) -> None:
    if not caminho.exists():
        return
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        os.environ.setdefault(chave.strip(), valor.strip())


_carregar_env(BASE / ".env")


def _destino(prefixo: str):
    chat = os.environ.get(f"{prefixo}_CHAT_ID", "").strip()
    thread = os.environ.get(f"{prefixo}_THREAD_ID", "").strip()
    if not chat:
        return None
    return {"chat_id": chat, "thread_id": int(thread) if thread else None}


TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()

DESTINOS = {
    "hardware": _destino("HARDWARE"),
    "perifericos": _destino("PERIFERICOS"),
    "jogos_gratis": _destino("JOGOS_GRATIS"),
}

# Chat da equipe que recebe as ofertas suspeitas para análise (vazio = descarta direto)
REVISAO = _destino("REVISAO")
REVISAO_HORAS = float(os.environ.get("REVISAO_HORAS", "2"))  # depois disso a oferta expira

# Canais públicos do Telegram usados como fonte extra (separados por vírgula)
CANAIS_FONTE = [c.strip().lstrip("@").replace("https://t.me/", "")
                for c in os.environ.get("CANAIS_FONTE", "").split(",") if c.strip()]

AMAZON_TAG = os.environ.get("AMAZON_TAG", "").strip()
ML_MATT_TOOL = os.environ.get("ML_MATT_TOOL", "").strip()
ML_MATT_WORD = os.environ.get("ML_MATT_WORD", "").strip()
# AliExpress: app da Open Platform (App Key/Secret) + Tracking ID do Portals
ALI_APP_KEY = os.environ.get("ALI_APP_KEY", "").strip()
ALI_APP_SECRET = os.environ.get("ALI_APP_SECRET", "").strip()
ALI_TRACKING_ID = os.environ.get("ALI_TRACKING_ID", "").strip()

# IA (Groq) para a frase criativa de cada oferta; vazio = sem frase
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_MODELO = os.environ.get("GROQ_MODELO", "").strip() or "openai/gpt-oss-120b"

INTERVALO_OFERTAS = int(os.environ.get("INTERVALO_OFERTAS_MIN", "5")) * 60
INTERVALO_JOGOS = int(os.environ.get("INTERVALO_JOGOS_MIN", "60")) * 60

# Divulgação
GRUPO_LINK = os.environ.get("GRUPO_LINK", "").strip()
TOP_DIA_HORA = int(os.environ.get("TOP_DIA_HORA", "20"))  # hora (Brasília) do Top 5 do dia

# Filtro de qualidade
MAX_IDADE_HORAS = float(os.environ.get("MAX_IDADE_HORAS", "24"))
PRECO_MINIMO = float(os.environ.get("PRECO_MINIMO", "20"))
DESCONTO_MINIMO = float(os.environ.get("DESCONTO_MINIMO", "10"))
DIAS_SEM_REPETIR = float(os.environ.get("DIAS_SEM_REPETIR", "3"))
MAX_POR_HORA = int(os.environ.get("MAX_POR_HORA", "8"))

# Pasta do estado e do log (no servidor/Docker, aponte DATA_DIR para um volume persistente)
DADOS = Path(os.environ.get("DATA_DIR", "").strip() or BASE)
DADOS.mkdir(parents=True, exist_ok=True)
ARQUIVO_ESTADO = DADOS / "estado.json"
