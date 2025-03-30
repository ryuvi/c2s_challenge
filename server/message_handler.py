import re
from unidecode import unidecode
from .repository import CarRepository
from typing import Optional, Tuple

class MessageHandler:
    """
    Classe responsável por processar e extrair informações de mensagens de texto relacionadas a veículos.

    Oferece métodos estáticos para normalização de texto e extração de:
    - Marcas e modelos de veículos
    - Faixas de preço
    - Cores
    - Tipos de combustível
    - Tipos de transmissão

    Todos os métodos realizam busques case-insensitive e com normalização de caracteres.
    """

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normaliza o texto para facilitar comparações e buscas.

        Args:
            text: Texto a ser normalizado

        Returns:
            str: Texto normalizado (minúsculo, sem acentos e espaços extras)

        Processo:
            1. Remove espaços no início/fim
            2. Converte para minúsculas
            3. Remove acentos e caracteres especiais
        """
        return unidecode(text.lower().strip())

    @staticmethod
    def extract_brand(text: str, repo: CarRepository) -> Optional[str]:
        """
        Extrai a marca do veículo de um texto, comparando com marcas conhecidas.

        Args:
            text: Texto contendo possivelmente uma marca de veículo
            repo: Repositório de dados de veículos

        Returns:
            Optional[str]: Nome da marca encontrada ou None se não encontrada

        Comportamento:
            - Faz busca case-insensitive
            - Retorna a primeira ocorrência encontrada
            - Usa a lista de marcas do repositório
        """
        known_brands = repo.get_unique_brands()
        normalized_text = MessageHandler.normalize_text(text)
        
        for brand in known_brands:
            if brand.lower() in normalized_text:
                return brand
        return None

    @staticmethod
    def extract_model(text: str, brand: str, repo: CarRepository) -> Optional[str]:
        """
        Extrai o modelo do veículo de um texto, considerando uma marca específica.

        Args:
            text: Texto contendo possivelmente um modelo de veículo
            brand: Marca do veículo para filtrar modelos
            repo: Repositório de dados de veículos

        Returns:
            Optional[str]: Nome do modelo encontrado ou None se não encontrado

        Observação:
            - Só busca modelos se a marca for fornecida
            - Faz busca case-insensitive
        """
        if not brand:
            return None
        
        known_models = repo.get_models_for_brand(brand)
        normalized_text = MessageHandler.normalize_text(text)
        
        for model in known_models:
            if model.lower() in normalized_text:
                return model
        return None

    @staticmethod
    def extract_price_range(text: str) -> Optional[Tuple[float, float]]:
        """
        Extrai faixa de preço de um texto usando expressões regulares.

        Args:
            text: Texto contendo informações de preço

        Returns:
            Optional[Tuple[float, float]]: Tupla com (min, max) ou None se não encontrado

        Padrões reconhecidos:
            - "entre R$ X e R$ Y" -> (X, Y)
            - "até R$ X" -> (0, X)
            - "acima de R$ X" -> (X, infinito)
            - "R$ X mil" -> (0, X*1000)

        Tratamento especial:
            - Substitui vírgulas por pontos em valores decimais
            - Remove pontos de separadores de milhar
            - Converte valores como "10 mil" para 10000
        """
        patterns = [
            # Padrão para intervalos (entre X e Y)
            r'(?:entre|de)\s*(?:R\$\s*)?(\d+[.,]?\d*)\s*(?:a|até|e)\s*(?:R\$\s*)?(\d+[.,]?\d*)',
            # Padrão para valores máximos (até X)
            r'(?:até|máximo)\s*(?:R\$\s*)?(\d+[.,]?\d*)',
            # Padrão para valores mínimos (acima de X)
            r'(?:acima de|mínimo)\s*(?:R\$\s*)?(\d+[.,]?\d*)',
            # Padrão para valores em milhares (X mil)
            r'(?:R\$\s*)?(\d+[.,]?\d*\s*(?:mil|k))'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    if len(match.groups()) == 2:  # Caso de intervalo
                        min_val = float(match.group(1).replace('.', '').replace(',', '.'))
                        max_val = float(match.group(2).replace('.', '').replace(',', '.'))
                        return (min_val, max_val)
                    else:  # Caso de valor único
                        value_str = match.group(1).lower()
                        if 'mil' in value_str or 'k' in value_str:
                            value = float(re.sub(r'[^\d.,]', '', value_str).replace(',', '.')) * 1000
                        else:
                            value = float(re.sub(r'[^\d.,]', '', value_str).replace(',', '.'))
                        
                        # Determina se é limite superior ou inferior
                        if 'até' in text or 'máximo' in text:
                            return (0.0, value)
                        else:
                            return (value, float('inf'))
                except ValueError:
                    continue
        return None

    @staticmethod
    def extract_color(text: str, repo: CarRepository) -> Optional[str]:
        """
        Extrai a cor do veículo de um texto.

        Args:
            text: Texto contendo possivelmente uma cor
            repo: Repositório com cores conhecidas

        Returns:
            Optional[str]: Cor encontrada ou None
        """
        known_colors = repo.data['cor'].dropna().unique().tolist()
        normalized_text = MessageHandler.normalize_text(text)
        
        for color in known_colors:
            if color.lower() in normalized_text:
                return color
        return None

    @staticmethod
    def extract_fuel(text: str, repo: CarRepository) -> Optional[str]:
        """
        Extrai o tipo de combustível de um texto.

        Args:
            text: Texto contendo possivelmente tipo de combustível
            repo: Repositório com combustíveis conhecidos

        Returns:
            Optional[str]: Combustível encontrado ou None
        """
        known_fuels = repo.data['combustivel'].dropna().unique().tolist()
        normalized_text = MessageHandler.normalize_text(text)
        
        for fuel in known_fuels:
            norm_fuel = MessageHandler.normalize_text(fuel.lower())
            if norm_fuel in normalized_text:
                return fuel
        return None

    @staticmethod
    def extract_transmission(text: str, repo: CarRepository) -> Optional[str]:
        """
        Extrai o tipo de transmissão de um texto.

        Args:
            text: Texto contendo possivelmente tipo de transmissão
            repo: Repositório com transmissões conhecidas

        Returns:
            Optional[str]: Transmissão encontrada ou None
        """
        known_transmissions = repo.data['transmissao'].dropna().unique().tolist()
        normalized_text = MessageHandler.normalize_text(text)
        
        for trans in known_transmissions:
            norm_trans = MessageHandler.normalize_text(trans)
            if norm_trans in normalized_text:
                return trans
        return None