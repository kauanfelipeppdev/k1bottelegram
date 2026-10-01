"""IA (API do Groq): frase criativa das ofertas e desempate na checagem de produto repetido.

Se GROQ_API_KEY não estiver configurada ou a API falhar, o bot segue sem a IA.
"""
import logging
import re

import requests

import config

log = logging.getLogger(__name__)

URL = "https://api.groq.com/openai/v1/chat/completions"

INSTRUCOES_LEGENDA = (
    "Você escreve para o K1 Ofertas, um grupo brasileiro de ofertas de hardware e periféricos gamer. "
    "Escreva UMA frase curta (no máximo 120 caracteres), divertida e criativa, que faça o leitor querer "
    "ver a oferta. Use linguagem de gamer brasileiro, pode ter no máximo 1 emoji. "
    "NÃO cite preço, desconto, loja nem especificações que não estejam no nome do produto. "
    "Não use hashtags nem aspas. Responda só com a frase."
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
        frase = _perguntar(INSTRUCOES_LEGENDA, f"Produto ({categoria}): {o['titulo']}", 0.9)
    except Exception as e:
        log.warning("Groq: não consegui gerar a frase (%s)", e)
        return None
    frase = re.sub(r"\s+", " ", frase).strip(" \"'“”")
    if not frase or len(frase) > 160:  # resposta fora do combinado: melhor sem frase
        return None
    return frase


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
