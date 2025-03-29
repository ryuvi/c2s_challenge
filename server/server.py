import zmq
import signal
import sys

from .database import DatabaseManager
from .conversation import ConversationManager
from .repository import CarRepository

class Server:
    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://127.0.0.1:5555")
        self.shutdown = False
        
        DatabaseManager.initialize_database()
        self.repo = CarRepository()
        self.conversation = ConversationManager(self.repo)
        
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        self.shutdown = True
        self.socket.close()
        self.context.term()
        sys.exit(0)

    def run(self):
        print("Servidor iniciado. Aguardando conexões...")
        print(f"Total de carros carregados: {len(self.repo.data)}")

        try:
            while not self.shutdown:
                try:
                    request = self.socket.recv_json(flags=zmq.NOBLOCK)
                    response = self.conversation.process_message(request.get('message', ''))
                    
                    if response.get('reset'):
                        self.conversation._reset_conversation()
                        
                    self.socket.send_json(response)
                    
                except zmq.Again:
                    continue
                    
        except Exception as e:
            print(f'Erro no servidor: {e}')
        finally:
            self.socket.close()
            self.context.term()