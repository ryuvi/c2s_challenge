import pandas as pd
import random
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from faker import Faker
from faker_vehicle import VehicleProvider
from .models import Car, Base, DATABASE_URL
from shared.constants import TRANSMISSOES, COMBUSTIVEIS, CORES

class DatabaseManager:
    """
    Gerenciador de banco de dados para a aplicação de veículos.

    Responsável por:
    - Inicialização da estrutura do banco de dados
    - População inicial com dados fictícios
    - Geração de registros aleatórios de veículos

    Utiliza:
    - SQLAlchemy para ORM e conexão com o banco
    - Faker para geração de dados fictícios
    """

    @staticmethod
    def initialize_database():
        """
        Inicializa o banco de dados, criando tabelas e populando dados iniciais se necessário.

        Fluxo:
        1. Cria engine de conexão com o banco
        2. Cria todas as tabelas definidas nos modelos
        3. Verifica se a tabela 'cars' está vazia
        4. Se vazia, popula com dados fictícios

        Tratamento de erros:
        - Se a tabela não existir ainda, trata o erro e força a população
        """
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(bind=engine)  # Cria todas as tabelas definidas nos modelos
        
        with engine.connect() as conn:
            try:
                # Verifica se já existem registros na tabela
                result = conn.execute(text("SELECT COUNT(*) FROM cars"))
                if result.scalar() == 0:  # Se tabela vazia
                    DatabaseManager.populate_database(engine)
            except Exception as e:
                print(f"Tabela ainda não existe ou erro ao verificar: {e}")
                # Força população se houver erro na verificação
                DatabaseManager.populate_database(engine)

    @staticmethod
    def populate_database(engine):
        """
        Popula o banco de dados com veículos fictícios.

        Args:
            engine: SQLAlchemy engine configurado para conexão com o banco

        Processo:
        1. Configura Faker com provedor de dados de veículos
        2. Gera 200 registros aleatórios
        3. Faz insert em lote

        Tratamento de erros:
        - Rollback em caso de falha
        - Fechamento garantido da sessão
        """
        fake = Faker('pt_BR')  # Configura Faker para dados em português
        fake.add_provider(VehicleProvider)  # Adiciona provedor de dados de veículos
        
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()  # Cria sessão para operações no banco

        try:
            # Gera 200 carros fictícios
            carros = [DatabaseManager.generate_car(fake) for _ in range(200)]
            db.add_all(carros)  # Insert em lote
            db.commit()  # Confirma transação
            print(f"Banco populado com {len(carros)} carros!")
        except Exception as e:
            db.rollback()  # Desfaz em caso de erro
            print(f"Erro ao popular banco: {e}")
        finally:
            db.close()  # Garante fechamento da sessão

    @staticmethod
    def generate_car(fake):
        """
        Gera um objeto Car com dados aleatórios.

        Args:
            fake: Instância do Faker configurada

        Returns:
            Car: Objeto Car com atributos aleatórios

        Dados gerados:
        - Marca, modelo, ano e categoria do Faker Vehicle
        - Demais atributos com valores aleatórios dentro de faixas realistas
        """
        # Gera atributos com distribuição aleatória
        portas = random.choice((2, 4))
        transmissao = random.choice(TRANSMISSOES)
        km = random.randint(0, 500000)  # Quilometragem entre 0 e 500.000 km
        combustivel = random.choice(COMBUSTIVEIS)
        motor = round(random.uniform(1.0, 6.0), 1)  # Motor entre 1.0 e 6.0
        cidade = round(random.uniform(5.0, 15.0), 2)  # Consumo urbano
        estrada = round(random.uniform(8.0, 20.0), 2)  # Consumo rodoviário
        preco = round(random.uniform(20000, 150000), 2)  # Preço entre 20k e 150k
        cor = random.choice(CORES)

        # Obtém dados básicos do veículo do Faker
        vehicle_object = fake.vehicle_object()

        return Car(
            marca=vehicle_object.get('Make'),
            modelo=vehicle_object.get('Model'),
            ano=vehicle_object.get('Year'),
            categoria=vehicle_object.get('Category'),
            combustivel=combustivel,
            quilometragem=km,
            transmissao=transmissao,
            qtt_portas=portas,
            motor=motor,
            consumo_cidade=cidade,
            consumo_estrada=estrada,
            preco=preco,
            cor=cor
        )