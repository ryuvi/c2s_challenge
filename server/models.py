from sqlalchemy import UUID, String, Integer, Float, Column
from sqlalchemy.orm import declarative_base
from uuid import uuid4
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = f'postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}'
Base = declarative_base()

class Car(Base):
    __tablename__ = "cars"

    id = Column(UUID, primary_key=True, index=True, default=uuid4)
    marca = Column(String, nullable=False)
    modelo = Column(String, nullable=False)
    ano = Column(Integer, nullable=False)
    categoria = Column(String, nullable=False)
    combustivel = Column(String, nullable=False)
    quilometragem = Column(Integer, nullable=False)
    transmissao = Column(String, nullable=False)
    qtt_portas = Column(Integer, nullable=False)
    motor = Column(Float, nullable=False)
    consumo_cidade = Column(Float, nullable=False)
    consumo_estrada = Column(Float, nullable=False)
    preco = Column(Float, nullable=False)
    cor = Column(String, nullable=False)