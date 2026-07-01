from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from engine import get_engine

session_db = sessionmaker(get_engine(), autoflush=False, autocommit=False)


@contextmanager
def db():
    session = session_db()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
