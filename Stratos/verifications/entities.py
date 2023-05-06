from sqlalchemy import Column
from db import Base
import sqlalchemy as db
import datetime


class Verification(Base):
    __tablename__ = 'verifications'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    card_number = Column(db.String(32))
    status = Column(db.Integer, default=0)
    comment = Column(db.Text)
    create_date = Column(db.DateTime, default=datetime.datetime.now)
    update_date = Column(db.DateTime, default=datetime.datetime.now)
    user_id = Column(db.Integer)
    user_email = Column(db.String(128))
    photo = Column(db.String(128))

    def __repr__(self):
        return '<Verify {} {} Status: {}>'.format(self.id, self.card_number, self.status)