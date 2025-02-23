import os
import telebot
import base64
import time
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InputFile
from dotenv import load_dotenv
from SHARED.mercadopago import gerar_pix_mercadopago, gerar_boleto_mercadopago, verificar_pagamento
from SHARED.database import atualizar_data_pagamento

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do bot
CHAVE_API = os.getenv('TOKENBOT2')
MERCADO_PAGO_ACCESS_TOKEN = os.getenv('MERCADO_PAGO_ACCESS_TOKEN_PROD')

# Verificar se as variáveis de ambiente foram carregadas corretamente
if not CHAVE_API or not MERCADO_PAGO_ACCESS_TOKEN:
    raise ValueError("Erro: Variáveis de ambiente não configuradas corretamente.")

# Inicializar o bot
bot = telebot.TeleBot(CHAVE_API)

# Dicionário para armazenar a assinatura escolhida por usuário
user_subscription = {}

# Valores das assinaturas
assinaturas = {
    "♦STANDARD | Mensal": 3.99,
    "⚜PREMIUM | Trimestral": 9.99,
    "♠VIP | Vitalício": 19.99
}

# Função para obter o ID do grupo correspondente
def obter_id_grupo(subscription_type):
    """
    Obtém o ID do grupo correspondente ao tipo de assinatura.
    :param subscription_type: Tipo de assinatura (mensal, trimestral, vitalício)
    :return: ID do grupo ou None se não encontrado
    """
    grupo_variavel = f"GRUPO_ID{subscription_type.upper()}"
    return os.getenv(grupo_variavel)

# Criar botões dinâmicos de pagamento
def criar_opcoes_pagamento():
    teclado_pagamento = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    teclado_pagamento.add(
        KeyboardButton(text="💳 Pagamento via PIX 📱"),
        KeyboardButton(text="💵 Pagamento via Boleto 📄"),
        KeyboardButton(text="↩️ Voltar")
    )
    return teclado_pagamento

# Criar botões dinâmicos de assinatura
def criar_opcoes_inline():
    teclado = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    for tipo, valor in assinaturas.items():
        # O texto do botão será exatamente o mesmo usado para identificar a assinatura
        teclado.add(KeyboardButton(text=f"{tipo} - R${valor:.2f}"))
    return teclado

# Comando /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        chat_id=message.chat.id,
        text="🌟 Olá! Bem-vindo ao nosso serviço! Escolha uma das opções abaixo:",
        reply_markup=criar_opcoes_inline()
    )

# Handler para seleção de assinatura
@bot.message_handler(func=lambda message: any(tipo in message.text for tipo in assinaturas.keys()))
def handle_assinatura(message):
    for tipo in assinaturas.keys():
        if tipo in message.text:
            user_subscription[message.chat.id] = tipo
            bot.send_message(
                message.chat.id,
                f"Você escolheu {tipo}! 🎉\nEscolha uma forma de pagamento abaixo:",
                reply_markup=criar_opcoes_pagamento()
            )
            return

# Verificação de pagamento
def verificar_pagamento_periodicamente(payment_id, chat_id, subscription_type):
    for tentativa in range(17):
        status = verificar_pagamento(payment_id)
        if status == "approved":
            atualizar_data_pagamento(chat_id, subscription_type)
            enviar_para_grupo(chat_id, subscription_type)
            return
        elif status == "pending":
            print(f"Pagamento pendente. Tentativa {tentativa + 1} de 17")
        else:
            print("Pagamento não aprovado ou rejeitado.")
            return
        time.sleep(30)
    bot.send_message(chat_id, "❌ Pagamento não confirmado após várias tentativas.")

# Enviar para o grupo (atualizado)
def enviar_para_grupo(chat_id, subscription_type):
    grupo_id = obter_id_grupo(subscription_type)
    if grupo_id:
        try:
            grupo_id_int = int(grupo_id)  # Converter para inteiro (ex: -1001234567890)
            # Tenta liberar o usuário (caso ele esteja bloqueado)
            try:
                bot.unban_chat_member(grupo_id_int, chat_id)
            except telebot.apihelper.ApiException:
                pass  # Ignora se não for possível desbanir

            # Gera um link de convite único (válido por 5 minutos e para 1 uso)
            link_info = bot.create_chat_invite_link(grupo_id_int, expire_date=int(time.time()) + 300, member_limit=1)
            link = link_info.invite_link
            bot.send_message(chat_id, f"🎉 Pagamento confirmado! Acesse o grupo através deste link único: {link}")
        except telebot.apihelper.ApiException as e2:
            bot.send_message(chat_id,
                             f"❌ Erro ao gerar o link do grupo: {e2.result_json['description']}. Contate o suporte.")
    else:
        bot.send_message(chat_id, "❌ ID do grupo não encontrado. Contate o suporte.")

# Handlers de pagamento
@bot.message_handler(func=lambda message: message.text == "💳 Pagamento via PIX 📱")
def handle_pix(message):
    user_id = message.chat.id
    subscription_type = user_subscription.get(user_id)
    if not subscription_type:
        return bot.send_message(user_id, "❌ Selecione uma assinatura primeiro.")

    pagamento = gerar_pix_mercadopago(assinaturas[subscription_type], f"Assinatura {subscription_type.capitalize()}")
    if pagamento:
        qr_code_bytes = base64.b64decode(pagamento["qr_code_base64"])
        with open("../SHARED/qr_code.png", "wb") as f:
            f.write(qr_code_bytes)
        with open("../SHARED/qr_code.png", "rb") as f:
            bot.send_photo(user_id, InputFile(f), caption="📸 Escaneie o QR Code para pagar via PIX")
        bot.send_message(user_id, f"🔑 Chave PIX: {pagamento['chave_pix']}\n\nCopie e cole no seu app de pagamentos.")
        verificar_pagamento_periodicamente(pagamento["payment_id"], user_id, subscription_type)
    else:
        bot.send_message(user_id, "❌ Erro ao gerar PIX. Tente novamente.")

@bot.message_handler(func=lambda message: message.text == "💵 Pagamento via Boleto 📄")
def handle_boleto(message):
    user_id = message.chat.id
    subscription_type = user_subscription.get(user_id)
    if not subscription_type:
        return bot.send_message(user_id, "❌ Selecione uma assinatura primeiro.")

    pagamento = gerar_boleto_mercadopago(assinaturas[subscription_type], f"Assinatura {subscription_type.capitalize()}")
    if pagamento:
        bot.send_message(user_id, f"🔗 Link do Boleto: {pagamento['link_boleto']}\n\nCopie e cole no navegador.")
        verificar_pagamento_periodicamente(pagamento["payment_id"], user_id, subscription_type)
    else:
        bot.send_message(user_id, "❌ Erro ao gerar boleto. Tente novamente.")

@bot.message_handler(func=lambda message: message.text == "↩️ Voltar")
def handle_voltar(message):
    user_subscription.pop(message.chat.id, None)
    bot.send_message(
        message.chat.id,
        "Escolha uma das opções abaixo:",
        reply_markup=criar_opcoes_inline()
    )

def start_bot2():
    print("Bot 2 está rodando...")
    bot.polling(none_stop=True)

if __name__ == "__main__":
    start_bot2()
    