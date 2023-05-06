from sqlalchemy import Column
from db import Base
import sqlalchemy as db
import datetime


class File(Base):
    __tablename__ = 'files'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    filename = Column(db.String(128))
    extension = Column(db.String(128))
    uuid = Column(db.String(128))