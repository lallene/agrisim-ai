import os
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./predictions.db")

connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    culture = Column(String, nullable=False)
    zone = Column(String, nullable=False)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    temperature = Column(Float, nullable=False)
    humidite = Column(Float, nullable=False)
    pluviometrie = Column(Float, nullable=False)

    type_sol = Column(String, nullable=False)
    ph = Column(Float, nullable=False)

    engrais = Column(Float, nullable=False)
    irrigation = Column(String, nullable=False)

    rendement_predit = Column(Float, nullable=False)
    date_prediction = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)