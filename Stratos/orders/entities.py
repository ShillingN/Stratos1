from sqlalchemy import Column
from db import Base
import sqlalchemy as db
import datetime
import tools
import decimal


class Order(Base):
    __tablename__ = 'orders'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    code = Column(db.String(32))
    client_id = Column(db.Integer)
    client_email = Column(db.String(128))
    tool_from = Column(db.String(128))
    tool_to = Column(db.String(128))
    give_amount = Column(db.DECIMAL(20, 8))
    receipt_amount = Column(db.DECIMAL(20, 8))
    give_rub = Column(db.DECIMAL(20, 2))
    receipt_rub = Column(db.DECIMAL(20, 2))
    current_cost = Column(db.DECIMAL(20, 2))

    from_wallet = Column(db.String(128), nullable=True)
    d_tag = Column(db.String(128), nullable=True)
    to_wallet = Column(db.String(128), nullable=True)
    exchange_wallet = Column(db.String(128))
    exchange_d_tag = Column(db.String(128), nullable=True)

    create_date = Column(db.DateTime, default=datetime.datetime.now)
    finish_date = Column(db.DateTime, default=None, nullable=True)
    status = Column(db.Integer, default=0)

    is_cash = Column(db.Boolean, default=False)
    cash_telegram = Column(db.String(128), nullable=True)
    cash_station = Column(db.String(128), nullable=True)
    cash_name = Column(db.String(128), nullable=True)

    ref_id = Column(db.String(64), nullable=True)
    tool_from_network = Column(db.String(64), nullable=True)
    tool_to_network = Column(db.String(64), nullable=True)

    secret_key = Column(db.String(64), nullable=True)

    operator_id = Column(db.String(64), nullable=True)
    payment_url = Column(db.String(128), nullable=True, default=None)
    cash_wallet = Column(db.String(256), default='')

    def get_status(self):
        if self.status == -1:
            return 'Заявка отменена'
        elif self.status == 0:
            return 'Новая сделка'
        elif self.status == 1:
            return 'Клиент перевёл'
        elif self.status == 2:
            return 'Депозит получен'
        elif self.status == 3:
            return 'Сделка завершена'

    def get_client_status(self):
        if self.status == -1:
            return 'Заявка отменена'
        elif self.status == 0:
            return 'Ожидает оплаты'
        elif self.status == 1:
            return 'Ожидает подтверждения'
        elif self.status == 2:
            return 'Депозит получен'
        elif self.status == 3:
            return 'Сделка завершена'

    def get_course(self):
        tool_from, tool_to = tools.api.get_tools_by_order(self)

        from_from = tool_from.name if len(tool_from.cost_link) == 0 else tool_from.cost_link
        from_to = tool_to.name if len(tool_to.cost_link) == 0 else tool_to.cost_link

        course = '1 {} к {} {}'.format(from_from, self.current_cost, from_to) if len(
            tool_from.cost_link) == 0 else '1 {} к {} {}'.format(from_to, self.current_cost, from_from)
        return course

    def get_html_info(self, additional_info=None):
        tool_from, tool_to = tools.api.get_tools_by_order(self)

        from_from = tool_from.name if len(tool_from.cost_link) == 0 else tool_from.cost_link
        from_to = tool_to.name if len(tool_to.cost_link) == 0 else tool_to.cost_link

        if tool_from.network is not None:
            from_from += tool_from.network

        if tool_to.network is not None:
            from_to += tool_to.network

        self.give_amount = self.give_amount.quantize(decimal.Decimal(tool_from.rounded_str))
        self.receipt_amount = self.receipt_amount.quantize(decimal.Decimal(tool_to.rounded_str))

        course = '1 {} к {} {}'.format(from_from, self.current_cost, from_to) if len(
            tool_from.cost_link) == 0 else '1 {} к {} {}'.format(from_to, self.current_cost, from_from)

        if additional_info is None:
            info = """Статус: <b>{}</b><br>
ID заявки: <b>{}</b><br>
Дата создания: <b>{}</b><br>
Курс обмена: <b>{}</b><br>
Сумма к отправлению: <b>{} {}</b><br>
На счет: <b>{} {}</b><br>
Сумма к получению: <b>{} {}</b><br>
На счет: <b>{}</b>""".format(
                self.get_status(),
                self.code,
                self.create_date.strftime('%d.%m.%Y %H:%M'),
                course,
                self.give_amount,
                from_from,
                self.exchange_wallet,
                self.exchange_d_tag if self.exchange_d_tag is not None else '',
                self.receipt_amount,
                from_to,
                self.to_wallet
            )
            if self.is_cash:
                info += '<br><br>Наличные: Да<br>Телефон: {}<br>Телеграм: {}<br>Имя: {}<br>Кошелёк: {}'.format(self.cash_station,
                                                                                            self.cash_telegram,
                                                                                            self.cash_name, self.cash_wallet)
            return info
        else:
            info = """{}\n\nСтатус: <b>{}</b><br>
ID заявки: <b>{}</b><br>
Дата создания: <b>{}</b><br>
Курс обмена: <b>{}</b><br>
Сумма к отправлению: <b>{} {}</b><br>
На счет: <b>{} {}</b><br>
Сумма к получению: <b>{} {}</b><br>
На счет: <b>{}</b>""".format(
                additional_info,
                self.get_status(),
                self.code,
                self.create_date.strftime('%d.%m.%Y %H:%M'),
                course,
                self.give_amount,
                from_from,
                self.exchange_wallet,
                self.exchange_d_tag if self.exchange_d_tag is not None else '',
                self.receipt_amount,
                from_to,
                self.to_wallet
            )
            if self.is_cash:
                info += '<br><br>Наличные: Да<br>Телефон: {}<br>Телеграм: {}<br>Имя: {}<br>Кошелёк: {}'.format(self.cash_station,
                                                                                            self.cash_telegram,
                                                                                            self.cash_name, self.cash_wallet)
            return info

    def get_info(self, additional_info=None):
        tool_from, tool_to = tools.api.get_tools_by_order(self)

        from_from = tool_from.name if len(tool_from.cost_link) == 0 else tool_from.cost_link
        from_to = tool_to.name if len(tool_to.cost_link) == 0 else tool_to.cost_link

        if tool_from.network is not None:
            from_from += tool_from.network

        if tool_to.network is not None:
            from_to += tool_to.network

        self.give_amount = self.give_amount.quantize(decimal.Decimal(tool_from.rounded_str))
        self.receipt_amount = self.receipt_amount.quantize(decimal.Decimal(tool_to.rounded_str))

        course = '1 {} к {} {}'.format(from_from, self.current_cost, from_to) if len(tool_from.cost_link) == 0 else '1 {} к {} {}'.format(from_to, self.current_cost, from_from)

        if additional_info is None:
            info = """Статус: {}
ID заявки: {}
Дата создания: {}
Курс обмена: {}
Сумма к отправлению: {} {}
На счет: {} {}
Сумма к получению: {} {}
На счет: {}""".format(
                self.get_status(),
                self.code,
                self.create_date.strftime('%d.%m.%Y %H:%M'),
                course,
                self.give_amount,
                from_from,
                self.exchange_wallet,
                self.exchange_d_tag if self.exchange_d_tag is not None else '',
                self.receipt_amount,
                from_to,
                self.to_wallet
            )
            if self.is_cash:
                info += '\n\nНаличные: Да\nТелефон: {}\nТелеграм: {}\nИмя: {}\nКошелёк: {}'.format(self.cash_station,
                                                                                            self.cash_telegram,
                                                                                            self.cash_name, self.cash_wallet)
            return info
        else:
            info = """{}\n\nСтатус: {}
ID заявки: {}
Дата создания: {}
Курс обмена: {}
Сумма к отправлению: {} {}
На счет: {} {}
Сумма к получению: {} {}
На счет: {}""".format(
                additional_info,
                self.get_status(),
                self.code,
                self.create_date.strftime('%d.%m.%Y %H:%M'),
                course,
                self.give_amount,
                from_from,
                self.exchange_wallet,
                self.exchange_d_tag if self.exchange_d_tag is not None else '',
                self.receipt_amount,
                from_to,
                self.to_wallet
            )
            if self.is_cash:
                info += '\n\nНаличные: Да\nТелефон: {}\nТелеграм: {}\nИмя: {}\nКошелёк: {}'.format(self.cash_station,
                                                                                            self.cash_telegram,
                                                                                            self.cash_name, self.cash_wallet)
            return info


    @staticmethod
    def get_status_by_id(status):
        if status == -1:
            return 'Заявка отменена'
        elif status == 0:
            return 'Новая сделка'
        elif status == 1:
            return 'Клиент перевёл'
        elif status == 2:
            return 'Депозит получен'
        elif status == 3:
            return 'Сделка завершена'


class Event(Base):
    __tablename__ = 'order_events'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    event = Column(db.Text)
    date = Column(db.DateTime, default=datetime.datetime.now)
    order_id = Column(db.Integer)


class RefTransaction(Base):
    __tablename__ = 'ref_transactions'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = Column(db.Integer)
    amount = Column(db.DECIMAL(16, 2))
    date = Column(db.DateTime, default=datetime.datetime.now)
    order_user_id = Column(db.Integer)
    order_user_email = Column(db.String(64))
    user_id = Column(db.Integer)
    user_email = Column(db.String(64))
