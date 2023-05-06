from sqlalchemy import Column
from db import Base
import sqlalchemy as db
import datetime


class Withdraw(Base):
    __tablename__ = 'withdraws'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    status = Column(db.Integer, default=0)
    code = Column(db.String(16))
    wallet = Column(db.String(256))
    user_id = Column(db.Integer)
    user_email = Column(db.String(64))
    amount = Column(db.DECIMAL(18, 6))
    amount_rub = Column(db.DECIMAL(18, 2))
    tool_name = Column(db.String(64))
    cost = Column(db.DECIMAL(18, 2))
    create_date = Column(db.DateTime, default=datetime.datetime.now)
    finish_date = Column(db.DateTime, default=None, nullable=True)
    comment = Column(db.Text)

    def get_status(self):
        if self.status == 0:
            return 'На модерации'
        if self.status == -1:
            return 'Отказано'
        if self.status == 1:
            return 'Выполнено'

    def get_round(self):
        if self.tool_name == 'BTC':
            return '0.000000'
        elif self.tool_name == 'USDT TRC20':
            return '0.00'
        else:
            return '0.00'

    @staticmethod
    def get_round_by_tool(tool_name):
        if tool_name == 'BTC':
            return '0.000000'
        elif tool_name == 'USDT TRC20':
            return '0.00'
        else:
            return '0.00'