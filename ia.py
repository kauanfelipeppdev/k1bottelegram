"""IA (API do Groq): frase curta das ofertas e desempate na checagem de produto repetido.

Se GROQ_API_KEY não estiver configurada ou a API falhar, o bot segue sem a IA.
"""
import logging
import re

import requests

import config

log = logging.getLogger(__name__)

URL = "https://api.groq.com/openai/v1/chat/completions"

INSTRUCOES_LEGENDA = (
    "Você escreve a legenda de ofertas do K1 Ofertas, um grupo brasileiro de hardware e periféricos gamer.\n"
    "Escreva UMA frase simples e natural (até 90 caracteres) dizendo para que o produto serve ou que "
    "vantagem ele traz no setup/jogo, como um amigo indicando a oferta.\n"
    "Regras:\n"
    "- Fale do produto real do título; não invente recursos, números ou especificações.\n"
    "- Tom leve e direto. Nada de exagero, metáforas, rimas, trocadilhos forçados ou frases de efeito.\n"
    "- Não cite preço, desconto, loja, frete ou cupom. Sem hashtags, aspas ou emojis.\n"
    "- Português do Brasil, sem gírias forçadas. Responda só com a frase.\n"
    "Exemplos bons:\n"
    "Suporte articulado para monitor -> Libera espaço na mesa e deixa o monitor na altura certa.\n"
    "SSD NVMe 1TB -> Jogos carregando bem mais rápido e espaço de sobra para a biblioteca.\n"
    "Mouse Logitech G203 -> Mouse leve e preciso, ótimo para quem joga FPS.\n"
    "Exemplos ruins (não faça): 'Domine o campo de batalha como um deus!', "
    "'Seu setup vai virar lenda e seus inimigos vão chorar', 'Partiu upar o FPS no talo, bora!'."
)

INSTRUCOES_REPETIDO = (
    "Você compara anúncios de lojas brasileiras. Diga se os dois anúncios são do MESMO produto "
    "(mesma marca e mesmo modelo; cor, versão de cabo/conexão ou texto do anúncio podem mudar). "
    "Modelos diferentes da mesma linha (ex.: G5 e G7, 4060 e 4070, 12400F e 13400F) NÃO são o mesmo. "
    "Responda apenas SIM ou NAO."
)


def _perguntar(instrucoes: str, texto: str, temperatura: float):
    dados = {
        "model": config.GROQ_MODELO,
        "messages": [{"role": "system", "content": instrucoes}, {"role": "user", "content": texto}],
        "temperature": temperatura,
        "max_tokens": 500,  # modelos que "pensam" gastam tokens antes de responder
    }
    if "gpt-oss" in config.GROQ_MODELO:
        dados["reasoning_effort"] = "low"
    r = requests.post(URL, timeout=15, headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"}, json=dados)
    r.raise_for_status()
    resposta = r.json()["choices"][0]["message"]["content"] or ""
    return re.sub(r"<think>.*?</think>", "", resposta, flags=re.S).strip()


def gerar_legenda(o: dict, tipo: str):
    """Retorna a frase, ou None."""
    if not config.GROQ_API_KEY:
        return None
    categoria = "hardware" if tipo == "hardware" else "periférico"
    try:
        frase = _perguntar(INSTRUCOES_LEGENDA, f"Produto ({categoria}): {o['titulo']}", 0.4)
    except Exception as e:
        log.warning("Groq: não consegui gerar a frase (%s)", e)
        return None
    frase = re.sub(r"\s+", " ", frase).strip(" \"'“”")
    frase = re.sub(r"^.*?->\s*", "", frase)  # caso a IA repita o formato dos exemplos
    if not _legenda_ok(frase):
        log.info("Groq: frase descartada: %s", frase)
        return None
    return frase


# Coisas que denunciam frase fora do combinado (preço, exagero, formato estranho).
_PROIBIDO = re.compile(
    r"r\$|\d+\s*%|\bdesconto|\bpreco|\bpreço|\bcupom|\bfrete|\bloja|#|\n|"
    r"\blend[aá]ri|\bdeus\b|\bbrabo|\binsano|\bdestru|\bdomin|\bbatalha|\bpartiu\b|\bbora\b",
    re.I)


def _legenda_ok(frase: str) -> bool:
    if not frase or not (15 <= len(frase) <= 110):
        return False
    if _PROIBIDO.search(frase):
        return False
    if frase.count("!") > 1 or len(re.findall(r"[.!?](?=\s|$)", frase)) > 1:
        return False  # mais de uma frase ou exclamação demais
    return True


def mesmo_produto(a: str, b: str) -> bool:
    """Pergunta à IA se dois títulos são do mesmo produto. Na dúvida (sem chave/erro), diz que não."""
    if not config.GROQ_API_KEY:
        return False
    try:
        resposta = _perguntar(INSTRUCOES_REPETIDO, f"Anúncio 1: {a}\nAnúncio 2: {b}", 0)
    except Exception as e:
        log.warning("Groq: não consegui comparar produtos (%s)", e)
        return False
    return resposta.upper().startswith("SIM")
