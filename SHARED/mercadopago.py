import os
import requests
import uuid
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Verifica se as variáveis de ambiente estão configuradas
ACCESS_TOKEN = os.getenv('MERCADO_PAGO_ACCESS_TOKEN_PROD')
if not ACCESS_TOKEN:
    raise ValueError("Token de acesso do Mercado Pago não encontrado. Verifique o arquivo .env.")

BASE_URL = "https://api.mercadopago.com/v1"

def _fazer_requisicao(url, payload=None, method="POST"):
    """
    Função interna para fazer requisições à API do Mercado Pago.
    :param url: URL da API
    :param payload: Dados da requisição (opcional para GET)
    :param method: Método HTTP (POST ou GET)
    :return: Resposta da API ou None em caso de erro
    """
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": str(uuid.uuid4())  # Gera um UUID único para cada requisição
    }

    try:
        if method == "POST":
            response = requests.post(url, json=payload, headers=headers)
        elif method == "GET":
            response = requests.get(url, headers=headers)
        else:
            raise ValueError("Método HTTP inválido. Use POST ou GET.")

        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")

        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"Erro na API do Mercado Pago: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Erro ao fazer requisição: {e}")
        return None

def criar_plano_assinatura(nome_plano, valor, periodo):
    """
    Cria um plano de assinatura no Mercado Pago.
    :param nome_plano: Nome do plano (ex: "Assinatura Mensal")
    :param valor: Valor do plano (ex: 6.99)
    :param periodo: Período de cobrança em meses (ex: 1 para mensal, 3 para trimestral)
    :return: Dados do plano ou None em caso de erro
    """
    url = f"{BASE_URL}/preapproval_plan"
    payload = {
        "auto_recurring": {
            "frequency": periodo,
            "frequency_type": "months",
            "transaction_amount": valor,
            "currency_id": "BRL"
        },
        "back_url": "https://seusite.com/retorno",
        "reason": nome_plano
    }
    return _fazer_requisicao(url, payload)

def gerar_pix_mercadopago(valor, descricao):
    """
    Gera um QR Code e uma chave PIX para pagamento via Mercado Pago.
    :param valor: Valor do pagamento (ex: 6.99)
    :param descricao: Descrição do pagamento (ex: "Assinatura Mensal")
    :return: Dicionário com QR Code, chave PIX e payment_id, ou None em caso de erro
    """
    url = f"{BASE_URL}/payments"
    payload = {
        "transaction_amount": valor,
        "description": descricao,
        "payment_method_id": "pix",
        "payer": {
            "email": "comprador@teste.com"  # Email do comprador (pode ser genérico)
        }
    }

    resposta = _fazer_requisicao(url, payload)
    if resposta:
        # Extrai o QR Code, chave PIX e payment_id da resposta
        qr_code_base64 = resposta["point_of_interaction"]["transaction_data"]["qr_code_base64"]
        qr_code = resposta["point_of_interaction"]["transaction_data"]["qr_code"]
        chave_pix = resposta["point_of_interaction"]["transaction_data"]["ticket_url"]
        payment_id = resposta["id"]

        return {
            "qr_code_base64": qr_code_base64,  # QR Code em base64 (para exibir como imagem)
            "qr_code": qr_code,  # Código QR Code em texto
            "chave_pix": chave_pix,  # Chave PIX para pagamento
            "payment_id": payment_id  # ID do pagamento (para verificação)
        }
    return None

def gerar_boleto_mercadopago(valor, descricao):
    """
    Gera um boleto bancário para pagamento via Mercado Pago.
    :param valor: Valor do pagamento (ex: 19.99)
    :param descricao: Descrição do pagamento (ex: "Assinatura Trimestral")
    :return: Dicionário com link do boleto e payment_id, ou None em caso de erro
    """
    url = f"{BASE_URL}/payments"
    payload = {
        "transaction_amount": valor,
        "description": descricao,
        "payment_method_id": "bolbradesco",  # Método de pagamento para boleto
        "payer": {
            "email": "comprador@teste.com",  # Email do comprador (pode ser genérico)
            "first_name": "Cliente",
            "last_name": "Teste",
            "identification": {
                "type": "CPF",
                "number": "12345678909"  # CPF do comprador (pode ser genérico)
            },
            "address": {
                "zip_code": "06233200",
                "street_name": "Rua Teste",
                "street_number": "123",
                "neighborhood": "Centro",
                "city": "São Paulo",
                "federal_unit": "SP"
            }
        }
    }

    resposta = _fazer_requisicao(url, payload)
    if resposta:
        # Extrai o link do boleto e payment_id da resposta
        link_boleto = resposta["transaction_details"]["external_resource_url"]
        payment_id = resposta["id"]

        return {
            "link_boleto": link_boleto,  # Link para pagamento do boleto
            "payment_id": payment_id  # ID do pagamento (para verificação)
        }
    return None

def verificar_pagamento(payment_id):
    """
    Verifica o status de um pagamento no Mercado Pago.
    :param payment_id: ID do pagamento (retornado ao gerar PIX ou boleto)
    :return: Status do pagamento ou None em caso de erro
    """
    url = f"{BASE_URL}/payments/{payment_id}"
    resposta = _fazer_requisicao(url, method="GET")
    if resposta:
        return resposta["status"]  # Retorna o status do pagamento (ex: "approved")
    return None

def verificar_status_assinatura(assinatura_id):
    """
    Verifica o status de uma assinatura no Mercado Pago.
    :param assinatura_id: ID da assinatura
    :return: Status da assinatura ou None em caso de erro
    """
    url = f"{BASE_URL}/preapproval/{assinatura_id}"
    resposta = _fazer_requisicao(url, method="GET")
    if resposta:
        return resposta["status"]  # Retorna o status da assinatura (ex: "authorized")
    return None