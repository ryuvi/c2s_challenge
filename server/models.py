from sqlalchemy import UUID, String, Integer, Float, Column
from sqlalchemy.orm import declarative_base
from uuid import uuid4
from dotenv import load_dotenv
import os

load_dotenv()
if os.getenv('DB_TYPE', 'sqlite') == 'sqlite':
    DATABASE_URL = f'sqlite:///{os.getenv("DB_NAME")}.sqlite'
    db_id_column = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid4()))
else:
    DATABASE_URL = f'postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}'
    db_id_column = Column(UUID, primary_key=True, index=True, default=uuid4)

Base = declarative_base()


class Car(Base):
    __tablename__ = "cars"

    id = db_id_column
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