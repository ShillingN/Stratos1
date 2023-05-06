from flask import blueprints, session, request, abort, redirect, render_template
from errors import *
from db import Session
import utils
import tools
import pairs
import decimal
import admin_log
import notify

app = blueprints.Blueprint('pairs', __name__, url_prefix='/api/pairs')


@app.route('/')
def home():
    return 'Pairs API'


@app.route('/create')
def create():
    user = utils.get_user(session)
    if user is None or user.admin < 2:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    tool_from = request.values.get('tool_from', 0, int)
    tool_to = request.values.get('tool_to', 0, int)
    fee = request.values.get('fee', 0.0, float)

    try:
        pair = pairs.api.create_pair(tool_from, tool_to, fee)
    except IncorrectDataValue as e:
        return utils.get_error(e.message)
    except Exception as e:
        return utils.get_error(e.args[0])
    return utils.get_answer('', {'pair': pair})


@app.route('/remove')
def remove():
    user = utils.get_user(session)
    if user is None or user.admin < 2:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    pair_id = request.values.get('id', 0, int)

    pairs.api.remove_pair_by_id(pair_id)

    return utils.get_answer('')


@app.route('/set/status')
def set_status():
    user = utils.get_user(session)
    if user is None or user.admin < 2:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    pair_id = request.values.get('id', 0, int)

    with Session() as db_session:
        pair = db_session.query(pairs.api.Pair).get(pair_id)
        if pair.status == 0:
            pair.status = 1
        else:
            pair.status = 0
        db_session.commit()

    return utils.get_answer('Сохранено')


@app.route('/set/fee')
def set_fee():
    user = utils.get_user(session)
    if user is None or user.admin < 2:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    pair_id = request.values.get('id', 0, int)
    fee = request.values.get('fee', 0.0, float)

    if fee < -100:
        return utils.get_error('Комиссия не может быть меньше -100%')
    if fee > 100:
        return utils.get_error('Комиссия не может быть больше 100%')

    db_session = Session()
    pair = db_session.query(pairs.api.Pair).get(pair_id)
    if pair is None:
        db_session.close()
        return utils.get_error('Такая пара не найдена')

    pair.fee = fee
    db_session.commit()
    db_session.close()

    return utils.get_answer('Сохранено')


@app.route('/set/value')
def set_value():
    user = utils.get_user(session)
    if user is None or user.admin < 2:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    pair_id = request.values.get('id', 0, int)
    value = request.values.get('value', 0.0, float)

    if value <= 0:
        return utils.get_error('Значение не может быть меньше или равно нулю')

    db_session = Session()
    pair = db_session.query(pairs.api.Pair).get(pair_id)
    if pair is None:
        db_session.close()
        return utils.get_error('Такая пара не найдена')

    cost = pair.get_stock_cost()
    new_fee = (value * 100 / cost) - 100
    new_fee = round(new_fee, 2)

    tool_from, tool_to = tools.api.get_tools_by_pair(pair)

    if len(tool_from.cost_link) > 0:
        new_fee = -new_fee
    pair.fee = new_fee
    db_session.commit()
    db_session.close()

    return utils.get_answer('Сохранено. Новая комиссия: {} %'.format(float(new_fee)))


@app.route('/set/min_max')
def set_min_max():
    user = utils.get_user(session)
    if user is None or user.admin < 2:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    pair_id = request.values.get('id', 0, int)
    min_payment = request.values.get('min_payment', 0.0, float)
    max_payment = request.values.get('max_payment', 0.0, float)

    if max_payment < 0:
        return utils.get_error('Значение не может быть меньше или равно нулю')

    if min_payment < 0:
        return utils.get_error('Значение не может быть меньше или равно нулю')

    db_session = Session()
    pair = db_session.query(pairs.api.Pair).get(pair_id)
    if pair is None:
        db_session.close()
        return utils.get_error('Такая пара не найдена')

    pair.min_payment = min_payment
    pair.max_payment = max_payment
    db_session.commit()
    db_session.close()

    return utils.get_answer('Сохранено')


@app.route('/get')
def get():
    user = utils.get_user(session)
    if user is None or user.admin < 1:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    pair_id = request.values.get('id', 0, int)

    pair = pairs.api.get_pair_by_id(pair_id)
    tool_from, tool_to = tools.api.get_tools_by_pair(pair)

    return utils.get_answer('', {'pair': pair, 'tool_from': tool_from, 'tool_to': tool_to})


@app.route('/best')
def best():
    user = utils.get_user(session)
    if user is None or user.admin < 2:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    pair_id = request.values.get('id', 0, int)
    best_position = request.values.get('position', 0, int)
    best_percent = request.values.get('percent', 0.0, float)

    best_percent = decimal.Decimal(best_percent).quantize(decimal.Decimal(0.00))

    if best_position < 0:
        return utils.get_error('Неверная позиция')

    db_session = Session()
    pair = db_session.query(pairs.api.Pair).get(pair_id)

    tool_from, tool_to = tools.api.get_tools_by_pair(pair)
    if len(tool_from.best_code) < 1:
        db_session.close()
        return utils.get_error('Укажите код BestChange для "Отдаёт"')
    if len(tool_to.best_code) < 1:
        db_session.close()
        return utils.get_error('Укажите код BestChange для "Получает"')

    pair.best_position = best_position
    pair.best_percent = best_percent
    db_session.commit()

    return utils.get_answer('Сохранено')


@app.route('/set/wallet')
def get_wallet():
    user = utils.get_user(session)
    if user is None or user.admin < 2:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    pair_id = request.values.get('id', 0, int)
    wallet = request.values.get('wallet', '', str)

    if len(wallet) == 0:
        wallet = None

    db_session = Session()
    pair = db_session.query(pairs.api.Pair).get(pair_id)
    pair.wallet = wallet
    db_session.commit()

    return utils.get_answer('Сохранено')


@app.route('/get/wallet')
def wallet():
    user = utils.get_user(session)
    if user is None or user.admin < 1:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    pair_id = request.values.get('id', 0, int)

    db_session = Session()
    pair = db_session.query(pairs.api.Pair).get(pair_id)
    wallet = pair.wallet if pair.wallet is not None else ''
    db_session.commit()
    db_session.close()

    return utils.get_answer('', {'wallet': wallet})


@app.route('/set/city')
def set_city():
    user = utils.get_user(session)
    if user is None or user.admin < 2:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    pair_id = request.values.get('id', 0, int)
    city = request.values.get('city', '', str)

    if len(city) == 0:
        city = None

    db_session = Session()
    pair = db_session.query(pairs.api.Pair).get(pair_id)
    pair.city = city
    db_session.commit()
    db_session.close()

    return utils.get_answer('Сохранено')


@app.route('/get/city')
def get_city():
    user = utils.get_user(session)
    if user is None or user.admin < 1:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    pair_id = request.values.get('id', 0, int)

    db_session = Session()
    pair = db_session.query(pairs.api.Pair).get(pair_id)
    city = pair.city if pair.city is not None else ''
    db_session.commit()
    db_session.close()

    return utils.get_answer('', {'city': city})


@app.route('/set/mass')
def set_mass():
    user = utils.get_user(session)
    if user is None or user.admin < 2:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    is_fiat = request.values.get('is_fiat', 0, int)
    new_percent = request.values.get('new_percent', 0.0, float)

    db_session = Session()
    pairs_list = db_session.query(pairs.api.Pair).all()
    tools_list = tools.api.get_tools()

    for pair in pairs_list:
        tool_from, tool_to = tools.api.get_tools_by_pair(pair, tools_list)
        if len(tool_from.cost_link) > 0:
            if is_fiat == 1:
                print(tool_from.name, tool_to.name, new_percent)
                pair.fee = new_percent
        else:
            if is_fiat == 0:
                print(tool_from.name, tool_to.name, new_percent)
                pair.fee = new_percent
    db_session.commit()
    db_session.close()

    return utils.get_answer('Сохранено.')



@app.before_request
def before():
    user = utils.get_user(session)
    if user is None:
        notify.hack_message(request, session)
        return abort(403)
    if user.admin == 0:
        notify.hack_message(request, session)
        return abort(403)