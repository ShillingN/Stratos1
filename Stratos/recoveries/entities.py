from sqlalchemy import Column
from db import Base
from uuid import uuid4
import sqlalchemy as db
import datetime


class Recovery(Base):
    __tablename__ = 'recoveries'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = Column(db.Integer)
    user_email = Column(db.String(64))
    code = Column(db.String(64), default=uuid4)
    create_date = Column(db.DateTime, default=datetime.datetime.now)
    status = Column(db.Integer, default=0)