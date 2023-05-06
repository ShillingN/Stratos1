from sqlalchemy import Column
from db import Base
import sqlalchemy as db
import datetime
import utils
import json


class PlanOrder(Base):
    __tablename__ = 'plan_orders'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    date = Column(db.DateTime)
    value = Column(db.DECIMAL(10, 2))
    ref_id = Column(db.String(128))
    status = Column(db.Boolean, default=False)


class AutoChange:
    def __init__(self):
        try:
            app_path = utils.get_script_dir()
            data = {}
            with open('{}/autochange.json'.format(app_path), 'r', encoding='utf-8') as f:
                data = json.loads(f.read())
            self.status = data['status']
            self.start_hour = data['start_hour']
            self.end_hour = data['end_hour']
            self.min_minutes = data['min_minutes']
            self.max_minutes = data['max_minutes']
            self.min_value = data['min_value']
            self.max_value = data['max_value']
            self.ref_id = data['ref_id']
            self.user_id = data['user_id']
        except:
            self.status = False
            self.start_hour = 10
            self.end_hour = 23
            self.min_minutes = 3
            self.max_minutes = 7
            self.min_value = 3000
            self.max_value = 5000
            self.ref_id = ''
            self.user_id = 0


    def save(self):
        app_path = utils.get_script_dir()

        data = {
            'status': self.status,
            'start_hour': self.start_hour,
            'end_hour': self.end_hour,
            'min_minutes': self.min_minutes,
            'max_minutes': self.max_minutes,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'ref_id': self.ref_id,
            'user_id': self.user_id,
        }

        with open('{}/autochange.json'.format(app_path), 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=4))