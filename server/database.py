import pandas as pd
import random

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from faker import Faker
from faker_vehicle import VehicleProvider

from .models import Car, Base, DATABASE_URL
from shared.constants import TRANSMISSOES, COMBUSTIVEIS, CORES

class DatabaseManager:
    @staticmethod
    def initialize_database():
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        
        with engine.connect() as conn:
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM cars"))
                if result.scalar() == 0:
                    DatabaseManager.populate_database(engine)
            except Exception as e:
                print(f"Tabela ainda não existe ou erro ao verificar: {e}")
                DatabaseManager.populate_database(engine)

    @staticmethod
    def populate_database(engine):
        fake = Faker('pt_BR')
        fake.add_provider(VehicleProvider)
        
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        try:
            carros = [DatabaseManager.generate_car(fake) for _ in range(200)]
            db.add_all(carros)
            db.commit()
            print(f"Banco populado com {len(carros)} carros!")
        except Exception as e:
            db.rollback()
            print(f"Erro ao popular banco: {e}")
        finally:
            db.close()

    @staticmethod
    def generate_car(fake):
        portas = random.choice((2, 4))
        transmissao = random.choice(TRANSMISSOES)
        km = random.randint(0, 500000)
        combustivel = random.choice(COMBUSTIVEIS)
        motor = round(random.uniform(1.0, 6.0), 1)
        cidade = round(random.uniform(5.0, 15.0), 2)
        estrada = round(random.uniform(8.0, 20.0), 2)
        preco = round(random.uniform(20000, 150000), 2)
        cor = random.choice(CORES)

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