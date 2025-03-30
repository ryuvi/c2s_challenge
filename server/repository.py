import pandas as pd
from sqlalchemy import create_engine
from typing import List, Dict
from .models import DATABASE_URL

class CarRepository:
    """
    Repositório para acesso e manipulação de dados de veículos.

    Esta classe fornece métodos para:
    - Carregar dados de carros de um banco de dados
    - Verificar existência de marcas e modelos
    - Listar marcas e modelos disponíveis
    - Buscar carros com filtros avançados

    Atributos:
        engine (sqlalchemy.engine.Engine): Conexão com o banco de dados
        data (pd.DataFrame): DataFrame contendo todos os dados de carros
    """

    def __init__(self):
        """
        Inicializa o repositório, criando a conexão com o banco e carregando os dados.
        """
        # Cria engine de conexão com o banco de dados
        self.engine = create_engine(DATABASE_URL)
        # Carrega os dados na memória como DataFrame
        self.data = self._load_data()

    def _load_data(self) -> pd.DataFrame:
        """
        Carrega os dados de carros do banco de dados para um DataFrame.

        Returns:
            pd.DataFrame: DataFrame contendo todos os registros da tabela 'cars'
        
        Notas:
            - Converte a coluna 'id' para string se existir
            - Todos os dados são carregados na memória para otimizar consultas
        """
        df = pd.read_sql_table('cars', self.engine)
        if 'id' in df.columns:
            df['id'] = df['id'].astype(str)  # Garante que IDs sejam tratados como strings
        return df

    def brand_exists(self, brand: str) -> bool:
        """
        Verifica se uma marca existe no repositório (busca case-insensitive).

        Args:
            brand: Nome da marca a ser verificada

        Returns:
            bool: True se a marca existe, False caso contrário
        """
        return not self.data[self.data['marca'].str.contains(brand, case=False)].empty

    def model_exists(self, model: str, brand: str) -> bool:
        """
        Verifica se um modelo existe para uma determinada marca (busca case-insensitive).

        Args:
            model: Nome do modelo a ser verificado
            brand: Nome da marca associada

        Returns:
            bool: True se o par marca/modelo existe, False caso contrário
        """
        brand_filter = self.data['marca'].str.contains(brand, case=False)
        model_filter = self.data['modelo'].str.contains(model, case=False)
        return not self.data[brand_filter & model_filter].empty

    def get_unique_brands(self) -> List[str]:
        """
        Retorna lista única de todas as marcas disponíveis, ordenadas alfabeticamente.

        Returns:
            List[str]: Lista de marcas únicas
        """
        return sorted(self.data['marca'].unique().tolist())

    def get_models_for_brand(self, brand: str) -> List[str]:
        """
        Retorna todos os modelos disponíveis para uma determinada marca (case-insensitive).

        Args:
            brand: Nome da marca para filtrar os modelos

        Returns:
            List[str]: Lista de modelos únicos para a marca, ordenados alfabeticamente
        """
        mask = self.data['marca'].str.contains(brand, case=False)
        return sorted(self.data[mask]['modelo'].unique().tolist())

    def search_cars(self, filters: Dict) -> List[Dict]:
        """
        Busca carros com base em múltiplos critérios de filtro.

        Args:
            filters: Dicionário com parâmetros de busca. Possíveis chaves:
                - marca: Nome da marca (busca parcial case-insensitive)
                - modelo: Nome do modelo (busca parcial case-insensitive)
                - preco_min: Preço mínimo
                - preco_max: Preço máximo
                - cor: Cor do veículo (busca parcial case-insensitive)
                - combustivel: Tipo de combustível (busca parcial case-insensitive)
                - transmissao: Tipo de transmissão (busca parcial case-insensitive)

        Returns:
            List[Dict]: Lista de dicionários contendo os carros que atendem aos filtros,
                      limitado a 20 resultados, ordenados conforme o DataFrame original
        """
        query = self.data.copy()  # Cria cópia para não modificar o DataFrame original
        
        # Aplica filtros cumulativos
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
        
        # Retorna no máximo 20 resultados no formato de dicionários
        return query.head(20).to_dict('records')