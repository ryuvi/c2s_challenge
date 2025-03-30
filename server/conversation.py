from .repository import CarRepository
from typing import Dict
from .message_handler import MessageHandler
from enum import Enum, auto
from shared.constants import CORES, COMBUSTIVEIS, TRANSMISSOES

class ConversationState(Enum):
    """
    Enumeração que representa os estados possíveis da conversa.
    
    Estados:
        WELCOME: Estado inicial de boas-vindas
        INIT: Estado inicial da conversa
        AWAITING_BRAND: Aguardando informação de marca
        AWAITING_MODEL: Aguardando informação de modelo
        AWAITING_PRECO: Aguardando informação de preço
        AWAITING_COR: Aguardando informação de cor
        AWAITING_COMBUSTIVEL: Aguardando informação de combustível
        AWAITING_TRANSMISSAO: Aguardando informação de transmissão
        READY_TO_SEARCH: Pronto para realizar a busca
    """
    WELCOME = auto()
    INIT = auto()
    AWAITING_BRAND = auto()
    AWAITING_MODEL = auto()
    AWAITING_PRECO = auto()
    AWAITING_COR = auto()
    AWAITING_COMBUSTIVEL = auto()
    AWAITING_TRANSMISSAO = auto()
    READY_TO_SEARCH = auto()

class ConversationManager:
    """
    Gerenciador de conversação para busca de veículos.

    Implementa uma máquina de estados que guia o usuário através do processo
    de especificação dos critérios de busca de veículos.

    Atributos:
        repo (CarRepository): Repositório de dados de veículos
        state (ConversationState): Estado atual da conversação
        filters (Dict[str, str]): Filtros acumulados para a busca
    """

    def __init__(self, repository: CarRepository):
        """
        Inicializa o gerenciador de conversação.

        Args:
            repository: Repositório de dados de veículos
        """
        self.repo = repository
        self.state = ConversationState.INIT  # Estado inicial
        self.filters: Dict[str, str] = {}  # Filtros acumulados

    def process_message(self, message: str) -> Dict:
        """
        Processa uma mensagem do usuário e retorna uma resposta apropriada.

        Args:
            message: Mensagem de texto do usuário

        Returns:
            Dict: Resposta contendo:
                - message: Texto de resposta
                - suggestions: Sugestões de opções (opcional)
                - results: Resultados da busca (opcional)
                - complete: Flag de conclusão (opcional)

        Comportamento:
            Roteia a mensagem para o handler apropriado baseado no estado atual
        """
        normalized = MessageHandler.normalize_text(message)  # Normaliza o texto para comparação
        
        # Roteamento baseado no estado atual
        if self.state == ConversationState.INIT:
            return self._handle_init()
        elif self.state == ConversationState.AWAITING_BRAND:
            return self._handle_brand_input(normalized)
        elif self.state == ConversationState.AWAITING_MODEL:
            return self._handle_model_input(normalized)
        elif self.state == ConversationState.AWAITING_PRECO:
            return self._handle_preco_input(normalized)
        elif self.state == ConversationState.AWAITING_COR:
            return self._handle_cor_input(normalized)
        elif self.state == ConversationState.AWAITING_COMBUSTIVEL:
            return self._handle_combustivel_input(normalized)
        elif self.state == ConversationState.AWAITING_TRANSMISSAO:
            return self._handle_transmissao_input(normalized)
        
        # Estado padrão caso não reconheça
        return {'message': "Como posso te ajudar?"}

    def _handle_init(self) -> Dict:
        """
        Manipula o estado inicial da conversa.
        
        Transiciona para o estado de aguardando marca e fornece sugestões.
        """
        self.state = ConversationState.AWAITING_BRAND
        return {
            'message': "Que legal! Vou te ajudar a encontrar o carro ideal. Qual marca você prefere?",
            'suggestions': self.repo.get_unique_brands()[:5]  # Top 5 marcas como sugestão
        }

    def _handle_brand_input(self, text: str) -> Dict:
        """
        Processa a entrada do usuário para marca do veículo.

        Args:
            text: Texto normalizado contendo possível marca

        Returns:
            Dict: Resposta apropriada baseada no reconhecimento da marca
        """
        brand = MessageHandler.extract_brand(text, self.repo)
        
        # Validação da marca
        if not brand:
            return {
                'message': "Não consegui identificar a marca. Poderia informar qual marca você prefere?",
                'suggestions': self.repo.get_unique_brands()[:5]
            }
            
        if not self.repo.brand_exists(brand):
            return {
                'message': f"Desculpe, não encontrei carros da marca {brand}. Alguma dessas marcas te interessa?",
                'suggestions': self.repo.get_unique_brands()[:5]
            }
            
        # Atualiza filtros e estado
        self.filters['marca'] = brand
        self.state = ConversationState.AWAITING_MODEL
        return {
            'message': f"Ótima escolha! Temos ótimos modelos da {brand}. Qual você prefere?",
            'suggestions': self.repo.get_models_for_brand(brand)[:5]  # Top 5 modelos da marca
        }

    def _handle_model_input(self, text: str) -> Dict:
        """
        Processa a entrada do usuário para modelo do veículo.

        Args:
            text: Texto normalizado contendo possível modelo

        Returns:
            Dict: Resposta apropriada baseada no reconhecimento do modelo
        """
        model = MessageHandler.extract_model(text, self.filters['marca'], self.repo)
        
        # Validação do modelo
        if not model:
            return {
                'message': "Não consegui identificar o modelo. Poderia informar qual modelo você deseja?",
                'suggestions': self.repo.get_models_for_brand(self.filters['marca'])[:5]
            }
            
        if not self.repo.model_exists(model, self.filters['marca']):
            return {
                'message': f"Desculpe, não encontrei o modelo {model} para {self.filters['marca']}. Algum desses te interessa?",
                'suggestions': self.repo.get_models_for_brand(self.filters['marca'])[:5]
            }
            
        # Atualiza filtros e estado
        self.filters['modelo'] = model
        self.state = ConversationState.AWAITING_PRECO
        return {
            'message': f"Excelente escolha! O {self.filters['marca']} {model} é um ótimo carro. Qual faixa de preço você está considerando?",
            'suggestions': [
                "Até 40.000",
                "Entre 40.000 e 60.000",
                "Entre 60.000 e 80.000",
                "Acima de 80.000"
            ]
        }

    def _handle_preco_input(self, text: str) -> Dict:
        """
        Processa a entrada do usuário para faixa de preço.

        Args:
            text: Texto normalizado contendo possível faixa de preço

        Returns:
            Dict: Resposta apropriada baseada no reconhecimento do preço
        """
        price_range = MessageHandler.extract_price_range(text)
        
        # Validação da faixa de preço
        if not price_range:
            return {
                'message': "Não consegui entender a faixa de preço.Poderia informar novamente? (Ex: 'até 50.000' ou 'entre 30.000 e 60.000')",
                'suggestions': [
                    "Até 40.000",
                    "Entre 40.000 e 60.000",
                    "Entre 60.000 e 80.000",
                    "Acima de 80.000"
                ]
            }
            
        # Atualiza filtros e estado
        self.filters['preco_min'], self.filters['preco_max'] = price_range
        self.state = ConversationState.AWAITING_COR
        return {
            'message': "Ótimo! Agora me diga:\nQual cor você prefere para o seu carro?",
            'suggestions': CORES[:5]  # Top 5 cores como sugestão
        }

    def _handle_cor_input(self, text: str) -> Dict:
        """
        Processa a entrada do usuário para cor do veículo.

        Args:
            text: Texto normalizado contendo possível cor

        Returns:
            Dict: Resposta apropriada baseada no reconhecimento da cor
        """
        cor = MessageHandler.extract_color(text, self.repo)
        
        # Validação da cor
        if not cor:
            return {
                'message': "Não consegui identificar a cor. Poderia informar qual cor você prefere?",
                'suggestions': CORES[:5]
            }
            
        # Atualiza filtros e estado
        self.filters['cor'] = cor
        self.state = ConversationState.AWAITING_COMBUSTIVEL
        return {
            'message': f"Boa escolha! {cor} é uma ótima cor. Qual tipo de combustível você prefere?",
            'suggestions': COMBUSTIVEIS[:3]  # Top 3 combustíveis como sugestão
        }

    def _handle_combustivel_input(self, text: str) -> Dict:
        """
        Processa a entrada do usuário para tipo de combustível.

        Args:
            text: Texto normalizado contendo possível combustível

        Returns:
            Dict: Resposta apropriada baseada no reconhecimento do combustível
        """
        combustivel = MessageHandler.extract_fuel(text, self.repo)
        
        # Validação do combustível
        if not combustivel:
            return {
                'message': "Não consegui identificar o combustível. Poderia informar qual tipo você prefere?",
                'suggestions': COMBUSTIVEIS[:3]
            }
            
        # Atualiza filtros e estado
        self.filters['combustivel'] = combustivel
        self.state = ConversationState.AWAITING_TRANSMISSAO
        return {
            'message': "Entendido! Só mais uma informação: Qual tipo de transmissão você deseja?",
            'suggestions': TRANSMISSOES  # Todas as opções de transmissão
        }
    
    def do_reset(self):
        """Reseta a conversação para o estado inicial."""
        self.state = ConversationState.INIT
        self.filters = {}

    def _handle_transmissao_input(self, text: str) -> Dict:
        """
        Processa a entrada do usuário para tipo de transmissão e retorna os resultados.

        Args:
            text: Texto normalizado contendo possível transmissão

        Returns:
            Dict: Resultados da busca ou mensagem de erro
        """
        transmissao = MessageHandler.extract_transmission(text, self.repo)
        
        # Validação da transmissão
        if not transmissao:
            return {
                'message': "Não consegui identificar a transmissão. Poderia informar qual tipo você prefere?",
                'suggestions': TRANSMISSOES
            }
            
        # Realiza a busca com todos os filtros
        self.filters['transmissao'] = transmissao
        results = self.repo.search_cars(self.filters)
        self._reset_conversation()
        
        # Retorna resultados ou mensagem de erro
        if not results:
            return {
                'message': "Que pena. Infelizmente não consegui encontrar nenhum resultado com esses filtros. Você quer tentar novamente com diferentes informações?",
                'reset': True  # Flag para indicar que pode reiniciar
            }
            
        return {
            'message': f"Ótimo! Encontrei {len(results)} carros que combinam com você:\n",
            'results': results,
            'complete': True  # Flag de conclusão
        }

    def _reset_conversation(self):
        """
        Reseta a conversação para um estado apropriado baseado no estado atual.
        
        Se estava aguardando transmissão, volta para aguardando marca.
        Caso contrário, volta para o estado inicial.
        """
        if self.state == ConversationState.AWAITING_TRANSMISSAO:
            self.state = ConversationState.AWAITING_BRAND  # Permite nova busca mantendo contexto
        else:
            self.state = ConversationState.INIT  # Reset completo
        self.filters = {}  # Limpa todos os filtros