import threading
from bot1 import start_bot1
from bot2 import start_bot2

# Cria threads para cada bot
thread1 = threading.Thread(target=start_bot1)
thread2 = threading.Thread(target=start_bot2)

# Inicia as threads
thread1.start()
thread2.start()

# Mantém o script principal rodando
thread1.join()
thread2.join()