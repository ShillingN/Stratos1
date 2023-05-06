from sqlalchemy import Column
from db import Base
import sqlalchemy as db
import datetime


class User(Base):
    __tablename__ = 'users'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    code = Column(db.String(8))
    create_date = Column(db.DateTime, default=datetime.datetime.now)
    email = Column(db.String(64))
    password = Column(db.String(64))

    ref_percent = Column(db.DECIMAL(10, 2))
    ref_balance = Column(db.DECIMAL(10, 2), default=0)
    ref_total_balance = Column(db.DECIMAL(10, 2), default=0)

    admin = Column(db.Integer, default=0)

    def __repr__(self):
        return '<User [{} {} {}]>'.format(self.id, self.code, self.email)