import re

from unidecode import unidecode
from .repository import CarRepository
from typing import Optional, Tuple

class MessageHandler:
    @staticmethod
    def normalize_text(text: str) -> str:
        return unidecode(text.lower().strip())

    @staticmethod
    def extract_brand(text: str, repo: CarRepository) -> Optional[str]:
        known_brands = repo.get_unique_brands()
        normalized_text = MessageHandler.normalize_text(text)
        
        for brand in known_brands:
            if brand.lower() in normalized_text:
                return brand
        return None

    @staticmethod
    def extract_model(text: str, brand: str, repo: CarRepository) -> Optional[str]:
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
        patterns = [
            r'(?:entre|de)\s*(?:R\$\s*)?(\d+[.,]?\d*)\s*(?:a|até|e)\s*(?:R\$\s*)?(\d+[.,]?\d*)',
            r'(?:até|máximo)\s*(?:R\$\s*)?(\d+[.,]?\d*)',
            r'(?:acima de|mínimo)\s*(?:R\$\s*)?(\d+[.,]?\d*)',
            r'(?:R\$\s*)?(\d+[.,]?\d*\s*(?:mil|k))'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    if len(match.groups()) == 2:
                        return float(match.group(1).replace('.', '').replace(',', '.')), float(match.group(2).replace('.', '').replace(',', '.'))
                    else:
                        value_str = match.group(1).lower()
                        if 'mil' in value_str or 'k' in value_str:
                            value = float(re.sub(r'[^\d.,]', '', value_str).replace(',', '.')) * 1000
                        else:
                            value = float(re.sub(r'[^\d.,]', '', value_str).replace(',', '.'))
                        return (0.0, value) if 'até' in text or 'máximo' in text else (value, float('inf'))
                except ValueError:
                    continue
        return None

    @staticmethod
    def extract_color(text: str, repo: CarRepository) -> Optional[str]:
        known_colors = repo.data['cor'].dropna().unique().tolist()
        normalized_text = MessageHandler.normalize_text(text)
        
        for color in known_colors:
            if color.lower() in normalized_text:
                return color
        return None

    @staticmethod
    def extract_fuel(text: str, repo: CarRepository) -> Optional[str]:
        known_fuels = repo.data['combustivel'].dropna().unique().tolist()
        normalized_text = MessageHandler.normalize_text(text)
        
        for fuel in known_fuels:
            norm_fuel = MessageHandler.normalize_text(fuel.lower())
            if norm_fuel in normalized_text:
                return fuel
        return None

    @staticmethod
    def extract_transmission(text: str, repo: CarRepository) -> Optional[str]:
        known_transmissions = repo.data['transmissao'].dropna().unique().tolist()
        normalized_text = MessageHandler.normalize_text(text)
        
        for trans in known_transmissions:
            norm_trans = MessageHandler.normalize_text(trans)
            if norm_trans in normalized_text:
                return trans
        return None
