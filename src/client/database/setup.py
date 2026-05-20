from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from api.database.models import Base as ApiBase
from client.database.models import Base as ClientBase
from client.config import settings

DB_URL = settings.get_db_url()

engine = create_engine(DB_URL, echo=True)


def create_db_and_tables() -> None:
    ApiBase.metadata.create_all(engine)
    ClientBase.metadata.create_all(engine)


Session = sessionmaker(engine)


def create_session():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
