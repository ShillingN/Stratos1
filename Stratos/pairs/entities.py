from sqlalchemy import Column
from db import Base
import sqlalchemy as db
import datetime
import tools
import whitebit
import decimal


class Pair(Base):
    __tablename__ = 'pairs'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    tool_from = Column(db.Integer)
    tool_to = Column(db.Integer)
    fee = Column(db.DECIMAL(10, 2))
    status = Column(db.Boolean, default=False)
    best_position = Column(db.Integer, default=0)
    best_percent = Column(db.DECIMAL, default=0)
    min_payment = Column(db.DECIMAL(16, 8), default=0)
    max_payment = Column(db.DECIMAL(16, 8), default=0)
    wallet = Column(db.String(128), default=None)
    city = Column(db.String(64), default=None, nullable=True)


    def get_stock_cost(self):
        t_from = tools.api.get_tool_by_id(self.tool_from)
        t_to = tools.api.get_tool_by_id(self.tool_to)

        if len(t_from.cost_link) > 0 and len(t_to.cost_link) > 0:
            cost = 1
            return cost

        if len(t_from.cost_link) > 0:
            cost_link = t_from.cost_link
            t_from = t_to.name
        else:
            cost_link = t_to.cost_link
            t_from = t_from.name

        cost = whitebit.api.get_cost(t_from, cost_link)
        if cost is None:
            cost_btc = whitebit.api.get_cost(t_from, 'USDT')
            cost = cost_btc * whitebit.api.get_cost('USDT', cost_link)
        return float(cost)


    def get_cost(self):
        t_from = tools.api.get_tool_by_id(self.tool_from)
        t_to = tools.api.get_tool_by_id(self.tool_to)

        fee = self.fee

        if len(t_from.cost_link) > 0 and len(t_to.cost_link) > 0:
            cost = 1
            cost = cost + ((cost * float(fee)) / 100)
            self.cost = float(cost)
            return self.cost

        if len(t_from.cost_link) > 0:
            self.rounded_str = t_to.rounded_str

            cost_link = t_from.cost_link
            t_from = t_to.name
            fee = -self.fee
        else:
            self.rounded_str = t_from.rounded_str

            cost_link = t_to.cost_link
            t_from = t_from.name

        cost = whitebit.api.get_cost(t_from, cost_link)
        if cost is None:
            cost_btc = whitebit.api.get_cost(t_from, 'BTC')
            cost = cost_btc * whitebit.api.get_cost('BTC', cost_link)

        self.stock_cost = float(cost)
        cost = cost + ((cost * float(fee)) / 100)
        self.cost = float(cost)
        return self.cost


    def is_fiat(self):
        t_from = tools.api.get_tool_by_id(self.tool_from)
        if len(t_from.cost_link) > 0:
            return True
        return False


    def get_min_max(self):
        t_from = tools.api.get_tool_by_id(self.tool_from)
        t_to = tools.api.get_tool_by_id(self.tool_to)

        if len(t_from.cost_link) > 0 and len(t_to.cost_link) > 0:
            if self.min_payment == 0:
                min_payment = t_from.min_payment
            else:
                min_payment = self.min_payment

            if self.max_payment == 0:
                max_payment = t_from.max_payment
            else:
                max_payment = self.max_payment

            self.min_from = min_payment
            self.max_from = max_payment
            self.min_from_local = min_payment - (min_payment / -self.fee)
            return

        self.cost = self.get_cost()

        if len(t_from.cost_link) > 0:
            if self.min_payment == 0:
                min_payment = t_from.min_payment
            else:
                min_payment = self.min_payment

            if self.max_payment == 0:
                max_payment = t_from.max_payment
            else:
                max_payment = self.max_payment

            self.min_from = min_payment
            self.max_from = max_payment

            self.min_from_local = decimal.Decimal(1 / self.cost * float(min_payment)).quantize(
                decimal.Decimal(self.rounded_str)
            )
        else:
            if t_to.is_cash is False:
                if self.min_payment == 0:
                    min_payment = t_from.min_payment
                else:
                    min_payment = self.min_payment

                if self.max_payment == 0:
                    max_payment = t_from.max_payment
                else:
                    max_payment = self.max_payment

                self.min_from_local = min_payment
                self.min_from = decimal.Decimal(1 / self.cost * float(min_payment)).quantize(
                    decimal.Decimal(self.rounded_str)
                )
                self.max_from = decimal.Decimal(1 / self.cost * float(max_payment)).quantize(
                    decimal.Decimal(self.rounded_str)
                )
            else:
                if self.min_payment == 0:
                    min_payment = t_to.min_payment
                else:
                    min_payment = self.min_payment

                if self.max_payment == 0:
                    max_payment = t_to.max_payment
                else:
                    max_payment = self.max_payment

                self.min_from_local = min_payment
                self.min_from = decimal.Decimal(1 / self.cost * float(min_payment)).quantize(
                    decimal.Decimal(self.rounded_str)
                )
                self.max_from = decimal.Decimal(1 / self.cost * float(max_payment)).quantize(
                    decimal.Decimal(self.rounded_str)
                )