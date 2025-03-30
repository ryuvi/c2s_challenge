import zmq
import signal
import sys
from .database import DatabaseManager
from .conversation import ConversationManager
from .repository import CarRepository

class Server:
    """
    Servidor de comunicação baseado em ZeroMQ para gerenciar interações com dados de carros.

    Esta classe implementa um servidor que:
    - Escuta mensagens em um socket ZMQ
    - Processa requisições através de um ConversationManager
    - Gerencia um repositório de dados de carros
    - Oferece controle seguro de desligamento

    Atributos:
        context (zmq.Context): Contexto ZeroMQ para comunicação
        socket (zmq.Socket): Socket REP (Reply) para comunicação
        shutdown (bool): Flag para controle de desligamento gracioso
        repo (CarRepository): Repositório de dados de carros
        conversation (ConversationManager): Gerenciador de diálogo
    """

    def __init__(self):
        """Inicializa o servidor, configurando socket, banco de dados e handlers."""
        # Configuração do ZeroMQ
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)  # Socket do tipo REP (Reply)
        self.socket.bind("tcp://0.0.0.0:5555")  # Escuta em todas as interfaces
        self.shutdown = False  # Flag para controle de desligamento

        # Inicialização do banco de dados e dependências
        DatabaseManager.initialize_database()
        self.repo = CarRepository()  # Repositório de dados
        self.conversation = ConversationManager(self.repo)  # Gerenciador de conversação

        # Configura handlers para sinais de desligamento
        signal.signal(signal.SIGINT, self.handle_shutdown)  # Captura Ctrl+C
        signal.signal(signal.SIGTERM, self.handle_shutdown)  # Captura kill command

    def handle_shutdown(self, signum, frame):
        """
        Handler para sinais de desligamento gracioso.

        Args:
            signum: Número do sinal recebido
            frame: Objeto de frame de execução atual
        """
        self.shutdown = True  # Ativa flag para encerrar loop principal

    def run(self):
        """
        Método principal que inicia o loop de processamento do servidor.

        Escuta mensagens continuamente até receber sinal de desligamento.
        Processa cada mensagem através do ConversationManager e envia respostas.
        """
        print("Servidor iniciado. Aguardando conexões...")
        print(f"Total de carros carregados: {len(self.repo.data)}")

        try:
            while not self.shutdown:
                try:
                    # Recebe requisição sem bloquear (permite verificar shutdown)
                    request = self.socket.recv_json(flags=zmq.NOBLOCK)
                    
                    # Processa comando especial de reset
                    if request.get('action', '') == 'reset':
                        self.conversation.do_reset()
                        continue
                    
                    # Processa mensagem normal e envia resposta
                    response = self.conversation.process_message(request.get('message', ''))
                    self.socket.send_json(response)
                    
                except zmq.Again:
                    # Não há mensagens disponíveis no momento
                    if self.shutdown:
                        break  # Sai se estiver desligando
                    continue  # Continua esperando mensagens
                    
        except Exception as e:
            print(f'Erro no servidor: {e}')
        finally:
            # Garante liberação adequada de recursos
            self._cleanup_resources()

    def _cleanup_resources(self):
        """Libera recursos de rede e contexto de forma segura."""
        try:
            if hasattr(self, 'socket') and self.socket:
                self.socket.close()  # Fecha socket de comunicação
        except Exception as e:
            print(f"Erro ao fechar socket: {e}")

        try:
            if hasattr(self, 'context') and self.context:
                self.context.term()  # Finaliza contexto ZeroMQ
        except Exception as e:
            print(f"Erro ao terminar contexto: {e}")