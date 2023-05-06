from flask import blueprints, session, request, abort, redirect, render_template
from errors import *
from db import Session
from .entities import Withdraw
import utils
import users
import datetime
import whitebit
import withdraws
import decimal
import notify
import admin_log

app = blueprints.Blueprint('Withdraws', __name__, url_prefix='/withdraws/api')


@app.route('/create')
def create():
    user = utils.get_user(session)
    if user is None:
        return abort(403)

    amount = request.values.get('amount', 0.0, float)
    tool = request.values.get('tool', '', str)
    wallet = request.values.get('wallet', '', str)

    try:
        withdraw = withdraws.api.create_withdraw(user, amount, tool, wallet)
    except IncorrectDataValue as e:
        return utils.get_error(e.message)
    except Exception as e:
        return utils.get_error(e.args[0])

    return utils.get_answer('', {'withdraw': withdraw})


@app.route('/balance')
def balance():
    user = utils.get_user(session)
    if user is None:
        return abort(403)

    tool = request.values.get('tool', '', str)

    round_function = Withdraw.get_round_by_tool(tool)

    if tool == 'USDT TRC20':
        cost = decimal.Decimal(whitebit.api.get_cost('USDT', 'RUB')).quantize(decimal.Decimal(round_function))
    elif tool == 'BTC':
        cost = decimal.Decimal(whitebit.api.get_cost('BTC', 'RUB')).quantize(decimal.Decimal(round_function))
    else:
        cost = decimal.Decimal(1).quantize(decimal.Decimal(round_function))
        tool = 'RUB'

    balance_ = decimal.Decimal(1) / cost * user.ref_balance
    total_balance = decimal.Decimal(1) / cost * user.ref_total_balance

    balance_ = balance_.quantize(decimal.Decimal(round_function))
    total_balance = total_balance.quantize(decimal.Decimal(round_function))

    return utils.get_answer('', {'balance': balance_, 'total_balance': total_balance, 'tool': tool})


@app.route('/set')
def set():
    user = utils.get_user(session)
    if user is None or user.admin < 2:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    withdraw_id = request.values.get('id', 0, int)
    status = request.values.get('status', 0, int)
    comment = request.values.get('comment', '', str)

    if status not in [1, -1]:
        return utils.get_error('Неверный статус')

    try:
        withdraws.api.change_status(user, withdraw_id, status, comment)
    except IncorrectDataValue as e:
        return utils.get_error(e.message)
    except Exception as e:
        return utils.get_error(e.args[0])

    return utils.get_answer('Сохранено')