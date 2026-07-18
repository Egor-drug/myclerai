from sqlalchemy import create_engine, String, Integer, Column, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime


DATABASE_Url = 'sqlite:///./admin.db'

engine = create_engine(DATABASE_Url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    register_at = Column(String, nullable=True)
    active = Column(Boolean, default=True)
    premium = Column(Boolean, default=False)  # Premium навсегда, если True
    crypto_invoice_id = Column(String, nullable=True)  # Для Crypto Bot


class BroadCast(Base):
    __tablename__ = 'broadcasts'
    id = Column(Integer, primary_key=True, index=True)
    message = Column(String, nullable=False)
    sent_at = Column(DateTime, default=datetime.datetime.now())


Base.metadata.create_all(bind=engine)