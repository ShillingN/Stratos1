from sqlalchemy import create_engine, event, exc
from sqlalchemy.pool import Pool
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import config

# engine = create_engine(config.DB_CONNECT, convert_unicode=True, pool_size=10, max_overflow=30)
engine = create_engine(config.DB_CONNECT, convert_unicode=True, pool_size=10, max_overflow=30)
#db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Session = sessionmaker(bind=engine)

Base = declarative_base()


@event.listens_for(Pool, "checkout")
def ping_connection(dbapi_connection, connection_record, connection_proxy):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SELECT 1")
    except:
        raise exc.DisconnectionError()
    cursor.close()


def init_db():
    # Здесь нужно импортировать все модули, где могут быть определены модели,
    # которые необходимым образом могут зарегистрироваться в метаданных.
    # В противном случае их нужно будет импортировать до вызова init_db()
    import users.entities
    import tools.entities
    import notify.entities
    import pairs.entities
    import files.entities
    import verifications.entities
    import orders.entities
    import withdraws.entities
    import recoveries.entities
    import kuna.entities
    import whitebit.entities
    Base.metadata.create_all(bind=engine)