import pandas as pd

from sqlalchemy import create_engine
from typing import List, Dict
from .models import DATABASE_URL

class CarRepository:
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.data = self._load_data()
        
    def _load_data(self) -> pd.DataFrame:
        df = pd.read_sql_table('cars', self.engine)
        if 'id' in df.columns:
            df['id'] = df['id'].astype(str)
        return df

    def brand_exists(self, brand: str) -> bool:
        return not self.data[self.data['marca'].str.contains(brand, case=False)].empty

    def model_exists(self, model: str, brand: str) -> bool:
        brand_filter = self.data['marca'].str.contains(brand, case=False)
        model_filter = self.data['modelo'].str.contains(model, case=False)
        return not self.data[brand_filter & model_filter].empty

    def get_unique_brands(self) -> List[str]:
        return sorted(self.data['marca'].unique().tolist())

    def get_models_for_brand(self, brand: str) -> List[str]:
        mask = self.data['marca'].str.contains(brand, case=False)
        return sorted(self.data[mask]['modelo'].unique().tolist())

    def search_cars(self, filters: Dict) -> List[Dict]:
        query = self.data.copy()
        
        if 'marca' in filters:
            query = query[query['marca'].str.contains(filters['marca'], case=False)]
        if 'modelo' in filters:
            query = query[query['modelo'].str.contains(filters['modelo'], case=False)]
        if 'preco_min' in filters and 'preco_max' in filters:
            query = query[(query['preco'] >= filters['preco_min']) & 
                         (query['preco'] <= filters['preco_max'])]
        if 'cor' in filters:
            query = query[query['cor'].str.contains(filters['cor'], case=False)]
        if 'combustivel' in filters:
            query = query[query['combustivel'].str.contains(filters['combustivel'], case=False)]
        if 'transmissao' in filters:
            query = query[query['transmissao'].str.contains(filters['transmissao'], case=False)]
        
        return query.head(20).to_dict('records')