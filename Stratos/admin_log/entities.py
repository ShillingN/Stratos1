from sqlalchemy import Column
from db import Base
import sqlalchemy as db
import datetime


class AdminLog(Base):
    __tablename__ = 'admin_logs'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    start_date = Column(db.DateTime, default=datetime.datetime.now)
    method = Column(db.String(32))
    url = Column(db.String(256))
    params = Column(db.JSON, default=None, nullable=True)
    headers = Column(db.JSON, default=None, nullable=True)
    email = Column(db.String(128))
    level = Column(db.Integer)