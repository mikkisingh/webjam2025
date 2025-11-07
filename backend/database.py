
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///app.db", echo=True)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)
