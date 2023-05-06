from db import Session
from .entities import Withdraw
from errors import *
import decimal
import whitebit
import users
import utils
import notify
import settings


def get_withdraws():
    with Session() as db_session:
        withdraws = db_session.query(Withdraw).all()
        withdraws.sort(key=lambda withdraw: withdraw.create_date, reverse=True)
    return withdraws


def get_withdraws_by_user_id(user_id):
    with Session() as db_session:
        withdraws = db_session.query(Withdraw).filter(Withdraw.user_id == user_id).all()
        withdraws.sort(key=lambda withdraw: withdraw.create_date, reverse=True)

        for withdraw in withdraws:
            if withdraw.status == 0:
                withdraw.badge = ''
                withdraw.icon = 'status_new'
            if withdraw.status == 1:
                withdraw.badge = 'success'
                withdraw.icon = 'accept'
            if withdraw.status == -1:
                withdraw.badge = 'danger'
                withdraw.icon = 'warn'
            withdraw.status_str = withdraw.get_status()

            withdraw.amount = decimal.Decimal(withdraw.amount).quantize(decimal.Decimal(withdraw.get_round()))

        return withdraws



def get_withdraw_by_code(code):
    with Session() as db_session:
        withdraw = db_session.query(Withdraw).filter(Withdraw.code == code).first()
    return withdraw


def change_status(admin, withdraw_id, status, comment=None):
    db_session = Session()
    withdraw = db_session.query(Withdraw).get(withdraw_id)
    if withdraw is None:
        db_session.close()
        raise IncorrectDataValue('Заявка с таким ID не найдена')

    if withdraw.status != 0:
        db_session.close()
        raise IncorrectDataValue('Неверный статус заявки')

    if status == -1 and (comment is None or len(comment) == 0):
        db_session.close()
        raise IncorrectDataValue('Необходимо указать комментарий')

    if status == -1:
        user = db_session.query(users.api.User).get(withdraw.user_id)
        user.ref_balance += withdraw.amount_rub
    if status == 1:
        comment = 'Одобрено {}'.format(admin.email)

    withdraw.status = status
    withdraw.comment = comment
    db_session.commit()
    db_session.close()


def create_withdraw(user, amount, tool, wallet):
    if float(amount) <= 0:
        raise IncorrectDataValue('Неверное значение')

    if len(wallet) < 3:
        raise utils.get_error('Укажите источник вывода')

    round_function = Withdraw.get_round_by_tool(tool)

    amount = decimal.Decimal(amount).quantize(decimal.Decimal(round_function))

    if tool == 'USDT TRC20':
        cost = decimal.Decimal(whitebit.api.get_cost('USDT', 'RUB')).quantize(decimal.Decimal(round_function))
    elif tool == 'BTC':
        cost = decimal.Decimal(whitebit.api.get_cost('BTC', 'RUB')).quantize(decimal.Decimal(round_function))
    else:
        cost = decimal.Decimal(1).quantize(decimal.Decimal(round_function))

    amount_rub = cost * amount

    setting = settings.Setting()

    if amount_rub < setting.min_withdraw:
        min_cost = decimal.Decimal(1) / cost * decimal.Decimal(setting.min_withdraw)
        raise IncorrectDataValue('Минимальная сумма вывода: {} {}'.format(min_cost.quantize(decimal.Decimal(round_function)), tool))

    if user.ref_balance < amount_rub:
        raise IncorrectDataValue('На вашем счету недостаточно средств для вывода {} {} ({} ₽)'.format(
            amount.quantize(decimal.Decimal(round_function)), tool, amount_rub.quantize(decimal.Decimal(round_function))
        ))

    with Session() as db_session:
        user_obj = db_session.query(users.api.User).get(user.id)
        user_obj.ref_balance -= amount_rub

        code = utils.get_random_code(6)
        check = get_withdraw_by_code(code)
        if check is not None:
            while check is not None:
                code = utils.get_random_code(6)
                check = get_withdraw_by_code(code)

        withdraw = Withdraw(user_id=user.id, user_email=user.email, amount=amount, amount_rub=amount_rub,
                            tool_name=tool, cost=cost, code=code, wallet=wallet)
        db_session.add(withdraw)
        db_session.commit()

    notify.send_message(
        f'Новая заявка на вывод реф. средств\n\nID: {code}\nПользователь: {user.email}\nСумма: {amount} {tool}\n'
        f'Кошелёк/карта: {wallet}'
    )

    return withdraw
