from sqlalchemy import Column
from db import Base
import sqlalchemy as db
import datetime


class WhitebitPayment(Base):
    __tablename__ = 'whitebit_payments'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    order_code = Column(db.String(16))
    order_secret = Column(db.String(64))
    payment_link = Column(db.String(256))
    deposit_id = Column(db.String(64))
    status = Column(db.Boolean, default=False)