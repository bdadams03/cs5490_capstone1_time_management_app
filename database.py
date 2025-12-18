from sqlalchemy import create_engine # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import sessionmaker # pyright: ignore[reportMissingImports]
engine=create_engine('sqlite:///focuspulse.db')
SessionLocal=sessionmaker(bind=engine)
