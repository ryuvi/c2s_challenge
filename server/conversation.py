from .repository import CarRepository
from typing import Dict
from .message_handler import MessageHandler
from enum import Enum, auto
from shared.constants import CORES, COMBUSTIVEIS, TRANSMISSOES

class ConversationState(Enum):
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
    def __init__(self, repository: CarRepository):
        self.repo = repository
        self.state = ConversationState.INIT
        self.filters: Dict[str, str] = {}

    def process_message(self, message: str) -> Dict:
        normalized = MessageHandler.normalize_text(message)
        
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
        return {'message': "Como posso te ajudar?"}

    def _handle_init(self) -> Dict:
        self.state = ConversationState.AWAITING_BRAND
        return {
            'message': "Que legal! Vou te ajudar a encontrar o carro ideal. Qual marca você prefere?",
            'suggestions': self.repo.get_unique_brands()[:5]
        }

    def _handle_brand_input(self, text: str) -> Dict:
        brand = MessageHandler.extract_brand(text, self.repo)
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
            
        self.filters['marca'] = brand
        self.state = ConversationState.AWAITING_MODEL
        return {
            'message': f"Ótima escolha! Temos ótimos modelos da {brand}. Qual você prefere?",
            'suggestions': self.repo.get_models_for_brand(brand)[:5]
        }

    def _handle_model_input(self, text: str) -> Dict:
        model = MessageHandler.extract_model(text, self.filters['marca'], self.repo)
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
        price_range = MessageHandler.extract_price_range(text)
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
            
        self.filters['preco_min'], self.filters['preco_max'] = price_range
        self.state = ConversationState.AWAITING_COR
        return {
            'message': "Ótimo! Agora me diga:\nQual cor você prefere para o seu carro?",
            'suggestions': CORES[:5]
        }

    def _handle_cor_input(self, text: str) -> Dict:
        cor = MessageHandler.extract_color(text, self.repo)
        if not cor:
            return {
                'message': "Não consegui identificar a cor. Poderia informar qual cor você prefere?",
                'suggestions': CORES[:5]
            }
            
        self.filters['cor'] = cor
        self.state = ConversationState.AWAITING_COMBUSTIVEL
        return {
            'message': f"Boa escolha! {cor} é uma ótima cor. Qual tipo de combustível você prefere?",
            'suggestions': COMBUSTIVEIS[:3]
        }

    def _handle_combustivel_input(self, text: str) -> Dict:
        combustivel = MessageHandler.extract_fuel(text, self.repo)
        if not combustivel:
            return {
                'message': "Não consegui identificar o combustível. Poderia informar qual tipo você prefere?",
                'suggestions': COMBUSTIVEIS[:3]
            }
            
        self.filters['combustivel'] = combustivel
        self.state = ConversationState.AWAITING_TRANSMISSAO
        return {
            'message': "Entendido! Só mais uma informação: Qual tipo de transmissão você deseja?",
            'suggestions': TRANSMISSOES
        }
    
    def do_reset(self):
        self.state = ConversationState.INIT

    def _handle_transmissao_input(self, text: str) -> Dict:
        transmissao = MessageHandler.extract_transmission(text, self.repo)
        if not transmissao:
            return {
                'message': "Não consegui identificar a transmissão. Poderia informar qual tipo você prefere?",
                'suggestions': TRANSMISSOES
            }
            
        self.filters['transmissao'] = transmissao
        results = self.repo.search_cars(self.filters)
        self._reset_conversation()
        
        if not results:
            return {
                'message': "Que pena. Infelizmente não consegui encontrar nenhum resultado com esses filtros. Você quer tentar novamente com diferentes informações?",
                'reset': True
            }
            
        return {
            'message': f"Ótimo! Encontrei {len(results)} carros que combinam com você:\n",
            'results': results,
            'complete': True
        }

    def _reset_conversation(self):
        if self.state == ConversationState.AWAITING_TRANSMISSAO:
            self.state = ConversationState.AWAITING_BRAND
        else:
            self.state = ConversationState.INIT
        self.filters = {}