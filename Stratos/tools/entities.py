from sqlalchemy import Column
from db import Base
import sqlalchemy as db
import datetime


class Tool(Base):
    __tablename__ = 'tools'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    name = Column(db.String(32))
    nickname = Column(db.String(32))
    wallet = Column(db.String(128), nullable=True)
    min_payment = Column(db.DECIMAL(10, 2), default=0)
    max_payment = Column(db.DECIMAL(10, 2), default=15000)
    reserve = Column(db.DECIMAL(20, 8), default=1000)
    sort_from = Column(db.Integer)
    sort_to = Column(db.Integer)
    showed = Column(db.Boolean, default=False)
    accept_count = Column(db.Integer, default=0)
    placeholder_from = Column(db.Text(64))
    placeholder_to = Column(db.Text(64))
    is_cash = Column(db.Boolean, default=False)
    rounded_str = Column(db.String(64), default='0.00')
    cost_link = Column(db.String(16), nullable=False, default='')
    xml_code = Column(db.String(16))
    network = Column(db.String(128), nullable=True)
    show_fio = Column(db.Boolean, default=False)
    best_code = Column(db.String(64), default='')
    best_city = Column(db.String(64), default='')

    def __repr__(self):
        return '<Tool {} {} {} [{} - {}]>'.format(self.id, self.name, self.nickname, self.min_payment, self.max_payment)