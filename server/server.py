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
        self.socket.bind("tcp://0.0.0.0:5555")
        self.shutdown = False
        
        DatabaseManager.initialize_database()
        self.repo = CarRepository()
        self.conversation = ConversationManager(self.repo)
        
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        self.shutdown = True

    def run(self):
        print("Servidor iniciado. Aguardando conexões...")
        print(f"Total de carros carregados: {len(self.repo.data)}")

        try:
            while not self.shutdown:
                try:
                    request = self.socket.recv_json(flags=zmq.NOBLOCK)
                    
                    if request.get('action', '') == 'reset':
                        self.conversation.do_reset()
                        continue
                    else:
                        response = self.conversation.process_message(request.get('message', ''))
                        self.socket.send_json(response)
                    
                except zmq.Again:
                    if self.shutdown:
                        break
                    continue
                    
        except Exception as e:
            print(f'Erro no servidor: {e}')
        finally:
            try:
                if hasattr(self, 'socket') and self.socket:
                    self.socket.close()
            except:
                pass

            try:
                if hasattr(self, 'context') and self.context:
                    self.context.term()
            except:
                pass