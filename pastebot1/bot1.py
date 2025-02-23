import threading
import telebot
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from SHARED.database import buscar_usuarios_expirados

# Carregar variáveis de ambiente
load_dotenv()

# Token do Bot 1
TOKEN_BOT1 = os.getenv('TOKENBOT1')

# IDs dos grupos (obtidos do .env)
GRUPO_ID_MENSAL = os.getenv('GRUPO_IDMENSAL')
GRUPO_ID_TRIMESTRAL = os.getenv('GRUPO_IDTRIMESTRAL')
GRUPO_ID_VITALICIO = os.getenv('GRUPO_IDVITALICIO')

# Verificar se todas as variáveis de ambiente foram carregadas corretamente
if not TOKEN_BOT1 or not GRUPO_ID_MENSAL or not GRUPO_ID_TRIMESTRAL or not GRUPO_ID_VITALICIO:
    raise ValueError("Erro: Algumas variáveis de ambiente não foram carregadas corretamente.")

# Inicializa o Bot 1
bot = telebot.TeleBot(TOKEN_BOT1)

def verificar_expiracao_assinaturas():
    """
    Verifica periodicamente se há usuários com assinaturas expiradas e os remove dos grupos correspondentes.
    """
    while True:
        try:
            usuarios_expirados = buscar_usuarios_expirados()
            for user_id, tipo_assinatura in usuarios_expirados:
                try:
                    grupo_id = {
                        'mensal': GRUPO_ID_MENSAL,
                        'trimestral': GRUPO_ID_TRIMESTRAL,
                        'vitalicio': GRUPO_ID_VITALICIO
                    }.get(    )  n

                    if grupo_id:
                        # Remove usuário com assinatura expirada
                        bot.kick_chat_member(grupo_id, user_id)
                        bot.unban_chat_member(grupo_id, user_id)  # Permite que ele entre novamente após expiração
                        print(f"Usuário {user_id} removido do grupo {grupo_id} devido à expiração da assinatura.")
                except Exception as e:
                    print(f"Erro ao remover usuário {user_id}: {e}")
            time.sleep(86400)  # Verifica uma vez por dia
        except Exception as e:
            print(f"Erro na verificação de expiração: {e}")
            time.sleep(3600)  # Espera 1 hora antes de tentar novamente

# Inicia a verificação de expiração em uma thread separada
threading.Thread(target=verificar_expiracao_assinaturas, daemon=True).start()

bot.polling(none_stop=True)
print("Bot 1 está rodando...")
