import re

def validar_chave_pix(tipo, chave):
    if tipo == "CPF":
        return re.fullmatch(r"\d{11}", chave) is not None
    elif tipo == "TELEFONE":
        return re.fullmatch(r"\d{11}", chave) is not None
    elif tipo == "E-MAIL":
        return re.fullmatch(r"[^@]+@[^@]+\.[^@]+", chave) is not None
    return False

def validar_valor(valor):
    try:
        return float(valor) > 0
    except ValueError:
        return False
