from sqlalchemy import Column
from db import Base
import sqlalchemy as db
import datetime


class TgUser(Base):
    __tablename__ = 'tg_users'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    tg_id = Column(db.BigInteger, nullable=False)