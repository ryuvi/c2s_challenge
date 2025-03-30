import zmq.asyncio
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static, Button, DataTable
from textual.containers import Vertical, Horizontal, ScrollableContainer
import asyncio
from rich.text import Text
from .utils import TAKE_NAME

class ChatApp(App):
    """
    Aplicação de chat para busca de veículos com interface textual e comunicação via ZMQ.

    Características:
    - Interface gráfica baseada em Textual
    - Comunicação assíncrona com servidor via ZeroMQ
    - Exibição de mensagens de chat e resultados em tabela
    - Estilização personalizada com CSS

    Atributos:
        _shutdown_lock (asyncio.Lock): Lock para controle de desligamento seguro
        zmq_context (zmq.asyncio.Context): Contexto ZMQ para comunicação
        client_socket (zmq.Socket): Socket para comunicação com o servidor
        poller (zmq.asyncio.Poller): Poller para recebimento assíncrono de mensagens
        results_table (DataTable): Widget para exibição dos resultados de busca
    """

    CSS = """
    /* Estilos CSS para a aplicação */
    Screen {
        layout: vertical;
    }
    #main_container {
        height: 1fr;
        width: 1fr;
    }
    #chat_output {
        height: 45%;
        border: round #666;
        padding: 1;
        overflow-y: auto;
    }
    #input_container {
        height: 15%;
        margin-top: 1;
    }
    #chat_input {
        width: 80%;
    }
    #send_button {
        width: 20%;
    }
    #results_container {
        height: 40%;
        border: round #666;
        margin: 1 0;
    }
    #results_table {
        height: 100%;
    }
    DataTable {
        background: $surface;
    }
    DataTable > .datatable--header {
        background: $accent;
        color: $text;
        text-style: bold;
    }
    DataTable > .datatable--cursor {
        background: $primary;
        color: $text;
    }
    .assistant-message {
        color: #4477ff;
    }
    .user-message {
        color: #44ff77;
    }
    .error-message {
        color: #ff4444;
    }
    """

    BINDINGS = [
        ('ctrl+q', 'quit', 'Sair'),  # Atalho para sair da aplicação
    ]

    def __init__(self):
        """
        Inicializa a aplicação, configurando os componentes de comunicação e interface.
        """
        super().__init__()
        # Controle de desligamento seguro
        self._shutdown_lock = asyncio.Lock()
        # Configuração do ZeroMQ
        self.zmq_context = None
        self.ctx = zmq.asyncio.Context()
        self.client_socket = None
        self.poller = zmq.asyncio.Poller()
        # Configuração da tabela de resultados
        self.results_table = DataTable(
            id="results_table",
            show_header=True,
            zebra_stripes=True,
            cursor_foreground_priority="renderable",
            fixed_rows=1
        )

    def compose(self) -> ComposeResult:
        """
        Compõe a interface gráfica da aplicação.

        Returns:
            ComposeResult: Estrutura hierárquica dos componentes da interface

        Layout:
            - Header: Cabeçalho da aplicação
            - Main Container:
                - Chat Output: Área de exibição de mensagens
                - Results Container: Área de exibição de resultados
                - Input Container: Área de entrada de mensagens
            - Footer: Rodapé da aplicação
        """
        yield Header()
        with Vertical(id="main_container"):
            with ScrollableContainer(id="chat_output"):
                yield Static("", id="chat_messages")
            with ScrollableContainer(id="results_container"):
                yield self.results_table
            with Horizontal(id="input_container"):
                yield Input(placeholder="Digite sua mensagem...", id="chat_input")
                yield Button("Enviar", id="send_button")
        yield Footer()

    async def on_mount(self) -> None:
        """
        Configuração inicial após montagem da interface.

        Tarefas:
        1. Configura colunas da tabela de resultados
        2. Conecta ao servidor
        3. Inicia task para escutar mensagens
        """
        # Configuração inicial da tabela
        self.results_table.add_columns(
            "Marca", "Modelo", "Ano", "Preço", "Cor", "Combustível", 
            "Transmissão", "KM", "Motor", "Portas"
        )
        self.results_table.display = False
        
        # Conexão e inicialização
        await self.connect_to_server()
        asyncio.create_task(self.listen_for_messages())

    async def connect_to_server(self):
        """
        Estabelece conexão com o servidor via ZeroMQ.

        Configura:
        - Socket REQ (Request) para comunicação
        - Poller para recebimento assíncrono
        """
        try:
            self.client_socket = self.ctx.socket(zmq.REQ)
            self.client_socket.connect("tcp://127.0.0.1:5555")
            self.poller.register(self.client_socket, zmq.POLLIN)
            self.display_message("✅ Conectado ao servidor de busca de veículos", "assistant")
            self.display_message(f"\n🔹 Olá {TAKE_NAME()}, como posso te ajudar hoje?", 'assistant')
        except Exception as e:
            self.display_message(f"❌ Erro na conexão: {e}", "error")

    async def listen_for_messages(self):
        """
        Escuta continuamente por mensagens do servidor.

        Processo:
        1. Usa poller para verificar mensagens de forma assíncrona
        2. Processa diferentes tipos de respostas:
           - Mensagens simples
           - Mensagens com sugestões
           - Mensagens com resultados
        """
        while True:
            try:
                events = await self.poller.poll(100)  # Poll com timeout de 100ms
                if self.client_socket in dict(events):
                    response = await self.client_socket.recv_json()
                    
                    message = response['message']
                    
                    # Adiciona sugestões se presentes
                    if 'suggestions' in response:
                        suggestions = "\nSugestões:\n💡 " + "\n💡 ".join(response['suggestions'])
                        message += suggestions
                    
                    self.display_message(f"\n🔹 Assistente: {message}", "assistant")
                    
                    # Exibe resultados se presentes
                    if 'results' in response:
                        await self.display_results(response['results'])
                        self.results_table.display = True
                    else:
                        self.results_table.display = False
                        
            except Exception as e:
                self.display_message(f"❌ Erro ao receber mensagem: {e}", "error")
                break
            await asyncio.sleep(0.1)  # Previne uso excessivo de CPU

    async def display_results(self, results):
        """
        Exibe os resultados de busca na tabela formatada.

        Args:
            results: Lista de dicionários contendo dados dos veículos

        Formatação especial:
        - Preço: Formato monetário com estilo verde
        - Quilometragem: Formato numérico com estilo cinza
        """
        self.results_table.clear()
        
        for car in results:
            # Formatação especial para preço (R$ 99.999,99)
            preco = Text(f'R$ {car.get("preco"):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'), style="green bold")
            # Formatação para quilometragem (99.999 km)
            km = Text(f"{car.get('quilometragem', 0):,} km", style="#888888")
            
            self.results_table.add_row(
                car.get('marca', ''),
                car.get('modelo', ''),
                str(car.get('ano', '')),
                preco,
                car.get('cor', ''),
                car.get('combustivel', ''),
                car.get('transmissao', ''),
                km,
                f"{car.get('motor', 0)}L",
                str(car.get('qtt_portas', ''))
            )

    async def send_message(self, message):
        """
        Envia mensagem para o servidor e atualiza a interface.

        Args:
            message: Texto da mensagem a ser enviada
        """
        if message and self.client_socket:
            self.display_message(f"🔸 Você: {message}", "user")
            try:
                await self.client_socket.send_json({"message": message})
            except Exception as e:
                self.display_message(f"❌ Erro: {e}", "error")
            self.query_one("#chat_input", Input).value = ""  # Limpa o input
        elif not message:
            self.display_message("❌ Por favor, digite uma mensagem.", "error")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        Handler para envio de mensagem via Enter.

        Args:
            event: Evento de submissão do input
        """
        user_message = event.value.strip()
        await self.send_message(user_message)
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Handler para envio de mensagem via botão.

        Args:
            event: Evento de clique no botão
        """
        await self.send_message(self.query_one("#chat_input", Input).value.strip())

    def display_message(self, message: str, message_type: str = "assistant"):
        """
        Exibe mensagem na área de chat com estilo apropriado.

        Args:
            message: Texto da mensagem
            message_type: Tipo de mensagem (assistant/user/error)
        """
        chat_messages = self.query_one("#chat_messages", Static)
        style_class = f" {message_type}-message" if message_type else ""
        message_html = f"[{style_class}]{message}[/]"
        
        # Mantém histórico e adiciona nova mensagem
        new_content = f"{chat_messages.renderable}\n{message_html}" if chat_messages.renderable else message_html
        chat_messages.update(new_content)
        self.query_one("#chat_output").scroll_end()  # Auto-scroll

if __name__ == "__main__":
    app = ChatApp()
    app.run()