from .entities import Order, Event, RefTransaction
from db import Session
from errors import *
from threading import Timer
from uuid import uuid4
from decimal import ROUND_CEILING
import config
import settings
import users
import tools
import decimal
import verifications
import utils
import datetime
import traceback
import notify
import kuna
import whitebit
import requests


def remove_ref_transaction(transaction_id):
    db_session = Session()
    ref_transaction = db_session.query(RefTransaction).get(transaction_id)
    order = db_session.query(Order).get(ref_transaction.order_id)

    if ref_transaction is None:
        db_session.close()
        raise IncorrectDataValue('Транзакция не найдена')

    ref_user = db_session.query(users.api.User).filter(users.api.User.id == ref_transaction.user_id).first()
    if ref_user is not None:
        ref_user.ref_balance -= ref_transaction.amount
        ref_user.ref_total_balance -= ref_transaction.amount
        event_ref = Event(event='Пользователю {} аннулирован реферальный бонус {} ₽. {}% от {} ₽'.format(
            ref_user.email, float(ref_transaction.amount), float(ref_user.ref_percent), float(order.give_rub)
        ), order_id=order.id)
        db_session.add(event_ref)
    db_session.delete(ref_transaction)
    db_session.commit()
    db_session.close()


def change_order_receipt_amount(order_id, amount, user):

    db_session = Session()
    order = db_session.query(Order).get(order_id)
    if order is None:
        db_session.close()
        raise IncorrectDataValue('Заявка с таким ID не найдена')

    amount = decimal.Decimal(amount)

    tool = tools.api.get_tool_by_name(order.tool_to, order.tool_to_network)
    if len(tool.cost_link) == 0:
        amount_rub = order.current_cost * amount
        amount_rub = amount_rub.quantize(decimal.Decimal('0.00'))
    else:
        amount_rub = amount.quantize(decimal.Decimal('0.00'))

    event_status = Event(event='{} изменил значение "Получает" с {} на {}'.format(user.email, order.receipt_amount.quantize(decimal.Decimal(tool.rounded_str)),
                                                                                  amount.quantize(decimal.Decimal(tool.rounded_str))),
                         order_id=order.id)
    db_session.add(event_status)

    order.receipt_amount = amount
    order.receipt_rub = amount_rub

    db_session.commit()
    db_session.close()


def change_order_give_amount(order_id, amount, user):
    db_session = Session()
    order = db_session.query(Order).get(order_id)
    if order is None:
        db_session.close()
        raise IncorrectDataValue('Заявка с таким ID не найдена')

    amount = decimal.Decimal(amount)

    tool = tools.api.get_tool_by_name(order.tool_from, order.tool_from_network)
    if len(tool.cost_link) == 0:
        amount_rub = order.current_cost * amount
        amount_rub = amount_rub.quantize(decimal.Decimal('0.00'))
    else:
        amount_rub = amount.quantize(decimal.Decimal('0.00'))

    event_status = Event(event='{} изменил значение "Отдаёт" с {} на {}'.format(user.email, order.give_amount.quantize(decimal.Decimal(tool.rounded_str)),
                                                                                amount.quantize(decimal.Decimal(tool.rounded_str))),
                         order_id=order.id)
    db_session.add(event_status)

    order.give_amount = amount
    order.give_rub = amount_rub

    db_session.commit()
    db_session.close()


def change_order_status(order_id, status, user=None, operator_id=None, source=None, owner=None):

    db_session = Session()
    order = db_session.query(Order).get(order_id)
    if order is None:
        db_session.close()
        raise IncorrectDataValue('Заявка с таким ID не найдена')

    who = user.email if user is not None else '[System]'
    if operator_id is not None:
        who = '[Оператор {}]'.format(operator_id)

    if owner is not None:
        who = '[{}]'.format(owner)

    event_status = Event(event='{} изменил статус сделки с {} на {}'.format(who, order.get_status(),
                                                                            Order.get_status_by_id(status)),
                         order_id=order.id)
    db_session.add(event_status)

    tool_from = db_session.query(tools.api.Tool).filter(tools.api.Tool.name == order.tool_from).first()
    tool_to = db_session.query(tools.api.Tool).filter(tools.api.Tool.name == order.tool_to).first()
    setting = settings.Setting()

    if status == 3 and order.status != 3:
        if setting.change_rests:
            tool_from.reserve += order.give_amount
            tool_to.reserve -= order.receipt_amount

        if order.ref_id is not None:
            ref_user = db_session.query(users.api.User).filter(users.api.User.code == order.ref_id).first()
            if ref_user is not None:
                amount = order.give_rub * ref_user.ref_percent / decimal.Decimal(100)
                amount = decimal.Decimal(amount).quantize(decimal.Decimal('0.00'))
                ref_user.ref_balance += amount
                ref_user.ref_total_balance += amount
                event_ref = Event(event='Пользователю {} начислен реф. бонус {} ₽. {}% от {} ₽'.format(
                    ref_user.email, float(amount), float(ref_user.ref_percent), float(order.give_rub)
                ), order_id=order.id)
                db_session.add(event_ref)

                ref_transaction = RefTransaction(order_id=order.id, amount=amount, order_user_id=order.client_id,
                                                 order_user_email=order.client_email, user_id=ref_user.id,
                                                 user_email=ref_user.email)

                # text = 'Вам начислен реферальный бонус от {}. Личный кабинет: {}'.format(order.client_email, config.DOMAIN_NAME)
                # utils.email(ref_user.email, 'StratosChange.ru: начислен реферальный бонус', text)
                db_session.add(ref_transaction)
        order.finish_date = datetime.datetime.now()

        message = f"""Сделка №{order.code} успешно завершена.

{order.receipt_amount} {order.tool_to} были отправлены Вам."""
        utils.email(order.client_email, 'StratosChange.ru: Депозит получен', message)

    if status == -1:
        order.finish_date = datetime.datetime.now()

    if status != 3 and order.status == 3:
        ref_transaction = db_session.query(RefTransaction).filter(RefTransaction.order_id == order.id).first()
        if ref_transaction is not None:
            ref_user = db_session.query(users.api.User).filter(users.api.User.id == ref_transaction.user_id).first()
            if ref_user is not None:
                ref_user.ref_balance -= ref_transaction.amount
                ref_user.ref_total_balance -= ref_transaction.amount
                event_ref = Event(event='Пользователю {} аннулирован реферальный бонус {} ₽. {}% от {} ₽'.format(
                    ref_user.email, float(ref_transaction.amount), float(ref_user.ref_percent), float(order.give_rub)
                ), order_id=order.id)
                db_session.add(event_ref)
            db_session.delete(ref_transaction)
        order.finish_date = None

    if status == 2 and order.status != 2 and source is not None:
        msg = 'Получен депозит от {}\n\n{}\n\nEmail: {}'.format(
            source, order.get_info(), order.client_email
        )
        notify.send_deposit_message(msg)

    if status == 2 and order.status != 2 and len(tool_to.cost_link) > 0:
        requests.get('http://91.219.63.40:2710/v1/orders/hook?amount={}'.format(order.receipt_rub))


    order.status = status
    if operator_id is not None:
        order.operator_id = operator_id
    db_session.commit()
    db_session.close()


def check_deals():
    setting = settings.Setting()

    db_session = Session()
    try:
        orders = db_session.query(Order).filter(Order.status == 0).all()

        now = datetime.datetime.now()
        for order in orders:
            diff = now.timestamp() - order.create_date.timestamp()
            print(diff / 60)
            if diff / 60 > setting.order_minutes:
                order.status = -1
                order.finish_date = now
                event = Event(event='Сделка закрыта по истечению таймера', order_id=order.id)
                db_session.add(event)

                message = f"""Сделка закрыта по истечению таймера
                Будем рады вас видеть в следующий раз у нас на сервисе.

                Информация о заявке:
                {order.get_info()}

                С уважением, администрация StratosChange"""
                utils.email(order.client_email, 'StratosChange.ru: Сделка отменена', message)
        db_session.commit()
    except:
        print(traceback.format_exc())
    finally:
        db_session.close()
        Timer(30, check_deals).start()


def get_events_by_order_id(order_id):
    with Session() as db_session:
        events = db_session.query(Event).filter(Event.order_id == order_id).all()
        events.sort(key=lambda event: event.date, reverse=True)
    return events


def get_orders_by_user_id(user_id, tools_list=None):
    with Session() as db_session:
        orders_list = db_session.query(Order).filter(Order.client_id == user_id).all()
        orders_list.sort(key=lambda order: order.create_date, reverse=True)

        if tools_list is None:
            tools_list = tools.api.get_tools()

        for order in orders_list:
            order.t_from = tools.api.get_tool_by_name(order.tool_from, order.tool_from_network, tools_list)
            order.t_to = tools.api.get_tool_by_name(order.tool_to, order.tool_to_network, tools_list)

            order.give_amount = order.give_amount.quantize(decimal.Decimal(order.t_from.rounded_str))
            print(order.tool_to)
            order.receipt_amount = order.receipt_amount.quantize(decimal.Decimal(order.t_to.rounded_str))

            order.status_str = order.get_status()

            order.icon = ''
            order.alert = ''
            if order.status == 0:
                order.icon = 'status_new'
                order.alert = ' '
            if order.status == -1:
                order.icon = 'user_red'
                order.alert = 'danger'
            if order.status == 2:
                order.icon = 'yellow_accept'
                order.alert = 'warning'
            if order.status == 3:
                order.icon = 'accept'
                order.alert = 'success'
            if order.status == 1:
                order.icon = 'yellow_accept'
                order.alert = 'warning'
        return orders_list


def get_ref_transactions_by_user_id(user_id):
    with Session() as db_session:
        ref_list = db_session.query(RefTransaction).filter(RefTransaction.user_id == user_id).all()
        ref_list.sort(key=lambda ref: ref.date, reverse=True)

        orders_list = get_orders()

        for ref in ref_list:
            ref.order = get_order_by_id(ref.order_id, orders_list)
        return ref_list


def get_ref_transactions():
    with Session() as db_session:
        ref_list = db_session.query(RefTransaction).all()
        ref_list.sort(key=lambda ref: ref.date, reverse=True)

        orders_list = get_orders()

        for ref in ref_list:
            ref.order = get_order_by_id(ref.order_id, orders_list)
        return ref_list


def get_order_by_id(order_id, orders_list=None):

    if orders_list is None:
        with Session() as db_session:
            order = db_session.query(Order).filter(Order.id == order_id).first()
        return order
    else:
        result = None
        for order in orders_list:
            if order.id == order_id:
                result = order
                break
        return result


def get_order_by_code(code, orders_list=None):
    if orders_list is None:
        with Session() as db_session:
            order = db_session.query(Order).filter(Order.code == code).first()
        return order
    else:
        result = None
        for order in orders_list:
            if order.code == code:
                result = order
                break
        return result


def get_order_by_secret_key(secret_key):
    with Session() as db_session:
        order = db_session.query(Order).filter(Order.secret_key == secret_key).first()
    return order


def get_order_by_wallet(wallet, d_tag):
    with Session() as db_session:
        order = db_session.query(Order).filter(Order.exchange_wallet == wallet, Order.exchange_d_tag == d_tag).first()
    return order


def get_orders():
    with Session() as db_session:
        orders = db_session.query(Order).all()
    return orders


def create_order(email, pair, give_amount, to_wallet, from_wallet=None, d_tag=None, cash_station=None,
                 cash_telegram=None, cash_name=None, ref_id=None, is_auto=False, cash_wallet=''):
    user = users.api.get_user_by_email(email)
    if user is None:
        user = users.api.create_user(email)

    setting = settings.Setting()
    if setting.tech_stop is True:
        raise IncorrectDataValue('Тех работы')

    tool_from = tools.api.get_tool_by_id(pair.tool_from)
    tool_to = tools.api.get_tool_by_id(pair.tool_to)

    if is_auto is False:
        if tool_from.showed is False:
            raise IncorrectDataValue('{} в данный момент недоступен для обмена'.format(tool_from.name))
        if tool_to.showed is False:
            raise IncorrectDataValue('{} в данный момент недоступен для обмена'.format(tool_to.name))

        ### Убрано 08.04 - StratosChange
        # if pair.is_fiat():
        #     verification = verifications.api.check_verification(from_wallet, user.email)
        #     if verification is False and tool_from.is_cash is False and tool_to.is_cash is False:
        #         return False

    pair.get_cost()

    give_amount = decimal.Decimal(give_amount).quantize(decimal.Decimal(tool_from.rounded_str), ROUND_CEILING)

    pair.get_min_max()

    if pair.is_fiat():
        receipt_amount = give_amount * (decimal.Decimal(1) / decimal.Decimal(pair.cost))
        give_rub = give_amount
        receipt_rub = give_amount
    else:
        receipt_amount = give_amount * decimal.Decimal(pair.cost)
        give_rub = give_amount * decimal.Decimal(pair.cost)
        receipt_rub = give_amount * decimal.Decimal(pair.cost)

    if len(tool_from.cost_link) > 0 and len(tool_to.cost_link) > 0:
        receipt_amount = give_rub + give_rub * (pair.fee / 100)
        give_rub = give_amount
        receipt_rub = give_rub * pair.fee
        print('{} * {} = {}'.format(give_rub, pair.fee, give_rub * pair.fee))


    receipt_amount.quantize(decimal.Decimal(tool_to.rounded_str), ROUND_CEILING)

    min_from = pair.min_from * decimal.Decimal(90) / decimal.Decimal(100)

    if is_auto is False:
        if give_amount < min_from:
            raise IncorrectDataValue('Введенная сумма обмена меньше минимальной ({})'.format(min_from))
        if give_amount > pair.max_from:
            raise IncorrectDataValue('Введенная сумма обмена больше максимальной ({})'.format(pair.max_from))

    code = utils.get_random_code(6)
    order_check = get_order_by_code(code)
    if order_check is not None:
        while order_check is not None:
            code = utils.get_random_code(6)
            order_check = get_order_by_code(code)

    exchange_wallet = tool_from.wallet
    exchange_d_tag = None
    if exchange_wallet == 'dynamic' and tool_from.is_cash is False:
        exchange_wallet, exchange_d_tag = whitebit.api.create_wallet(tool_from)

    if pair.wallet is not None:
        exchange_wallet = pair.wallet

    is_cash = True if tool_to.is_cash or tool_from.is_cash else False

    if len(ref_id) == 0:
        ref_id = None

    secret_key = str(uuid4())

    order = Order(code=code, client_id=user.id, client_email=user.email, tool_from=tool_from.name, tool_to=tool_to.name,
                  give_amount=give_amount, receipt_amount=receipt_amount, give_rub=give_rub, receipt_rub=receipt_rub,
                  current_cost=pair.cost, from_wallet=from_wallet, d_tag=d_tag, to_wallet=to_wallet,
                  exchange_wallet=exchange_wallet, exchange_d_tag=exchange_d_tag, is_cash=is_cash, cash_name=cash_name,
                  cash_telegram=cash_telegram, cash_station=cash_station, tool_from_network=tool_from.network,
                  tool_to_network=tool_to.network, ref_id=ref_id, secret_key=secret_key, cash_wallet=cash_wallet)

    action = 'переведите'

    with Session() as db_session:
        db_session.add(order)
        db_session.commit()

        order = get_order_by_code(code)

        if is_auto is False:
            event = Event(event='Заявка создана', order_id=order.id)
            db_session.add(event)
            db_session.commit()
        else:
            event = Event(event='[Автообмен] Заявка создана', order_id=order.id)
            db_session.add(event)
            db_session.commit()

    if order.exchange_wallet == 'kuna':
        kuna.api.get_payment(order)
        payment = kuna.api.get_payment_by_order_code(order.code)
        order.payment_url = payment.payment_link
        action = 'оплатите'

    if order.exchange_wallet == 'whitebit':
        whitebit.api.get_payment(order)
        payment = whitebit.api.get_payment_by_order_code(order.code)
        order.payment_url = payment.payment_link
        action = 'оплатите'

    setting = settings.Setting()
    deadline = datetime.datetime.now().timestamp() + setting.order_minutes * 60
    deadline = datetime.datetime.fromtimestamp(deadline)

    if is_auto is False:
        message = f"""Здравствуйте!
Вы создали заявку на обмен.
Ваша ссылка {config.DOMAIN_NAME}/status/{secret_key}
    
Информация о заявке:
{order.get_info()}
    
Пожалуйста, {action} указанную сумму по заявке до {deadline.strftime('%d.%m.%Y %H:%M')}. В противном случае заявка будет аннулирована.
    
С уважением, администрация StratosChange"""
        utils.email(email, 'StratosChange.ru: заявка на обмен успешно создана', message)

    if is_auto is False:
        notify.send_message(
            f'Новая заявка на обмен\n\n{(order.get_info())}\n\nEmail: {email}'
        )

    return order


def search_orders(orders_list, query):
    result = []

    query = str(query).lower()

    for order in orders_list:
        order_dict = order.__dict__
        for attr_name in order_dict:
            try:
                value = str(order_dict[attr_name]).lower()
            except:
                continue
            if query in value:
                result.append(order)
    return result