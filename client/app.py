import zmq.asyncio
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static, Button, DataTable
from textual.containers import Vertical, Horizontal, ScrollableContainer
import asyncio
from rich.text import Text
from .utils import TAKE_NAME

class ChatApp(App):
    """Aplicação de chat com Textual + ZMQ (assíncrona)"""

    CSS = """
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
        ('ctrl+q', 'quit', 'Sair'),
    ]

    def __init__(self):
        super().__init__()
        self._shutdown_lock = asyncio.Lock()
        self.zmq_context = None
        self.ctx = zmq.asyncio.Context()
        self.client_socket = None
        self.poller = zmq.asyncio.Poller()
        self.results_table = DataTable(
            id="results_table",
            show_header=True,
            zebra_stripes=True,
            cursor_foreground_priority="renderable",
            fixed_rows=1
        )

    def compose(self) -> ComposeResult:
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
        self.results_table.add_columns(
            "Marca", "Modelo", "Ano", "Preço", "Cor", "Combustível", 
            "Transmissão", "KM", "Motor", "Portas"
        )
        self.results_table.display = False
        
        await self.connect_to_server()
        asyncio.create_task(self.listen_for_messages())

    async def connect_to_server(self):
        try:
            self.client_socket = self.ctx.socket(zmq.REQ)
            self.client_socket.connect("tcp://127.0.0.1:5555")
            self.poller.register(self.client_socket, zmq.POLLIN)
            self.display_message("✅ Conectado ao servidor de busca de veículos", "assistant")
            self.display_message(f"\n🔹 Olá {TAKE_NAME()}, como posso te ajudar hoje?", 'assistant')
        except Exception as e:
            self.display_message(f"❌ Erro na conexão: {e}", "error")

    async def listen_for_messages(self):
        while True:
            try:
                events = await self.poller.poll(100)
                if self.client_socket in dict(events):
                    response = await self.client_socket.recv_json()
                    
                    # Processa a mensagem principal
                    message = response['message']
                    
                    # Adiciona sugestões se existirem
                    if 'suggestions' in response:
                        suggestions = "\nSugestões:\n💡 " + "\n💡 ".join(response['suggestions'])
                        message += suggestions
                    
                    self.display_message(f"\n🔹 Assistente: {message}", "assistant")
                    
                    # Se houver resultados, mostra na tabela
                    if 'results' in response:
                        await self.display_results(response['results'])
                        self.results_table.display = True
                    else:
                        self.results_table.display = False
                        
            except Exception as e:
                self.display_message(f"❌ Erro ao receber mensagem: {e}", "error")
                break
            await asyncio.sleep(0.1)

    async def display_results(self, results):
        """Exibe os resultados na tabela formatada"""
        self.results_table.clear()
        
        for car in results:
            preco = Text(f'R$ {car.get("preco"):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'), style="green bold")
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
        if message and self.client_socket:
            self.display_message(f"🔸 Você: {message}", "user")
            try:
                await self.client_socket.send_json({"message": message})
            except Exception as e:
                self.display_message(f"❌ Erro: {e}", "error")
            self.query_one("#chat_input", Input).value = ""
        elif not message:
            self.display_message("❌ Por favor, digite uma mensagem.", "error")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        user_message = event.value.strip()
        await self.send_message(user_message)
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        await self.send_message(self.query_one("#chat_input", Input).value.strip())

    def display_message(self, message: str, message_type: str = "assistant"):
        chat_messages = self.query_one("#chat_messages", Static)
        style_class = f" {message_type}-message" if message_type else ""
        message_html = f"[{style_class}]{message}[/]"
        
        new_content = f"{chat_messages.renderable}\n{message_html}" if chat_messages.renderable else message_html
        chat_messages.update(new_content)
        self.query_one("#chat_output").scroll_end()

if __name__ == "__main__":
    app = ChatApp()
    app.run()