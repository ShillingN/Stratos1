from flask import blueprints, session, request, abort, redirect, render_template
from errors import *
from db import Session
import utils
import tools
import pairs
import decimal
import orders
import settings
import autochange
import users
import traceback
import admin_log
import notify

app = blueprints.Blueprint('API', __name__, url_prefix='/v1/api')

create_tokens = []


@app.before_request
def before():
    setting = settings.Setting()
    if setting.tech_stop is True:
        user = utils.get_user(session)
        if user is None or user.admin < 1:
            notify.hack_message(request, session)
            return abort(400)


@app.route('/')
def home():
    return 'StratosChange API'


@app.route('/auth', methods=['POST'])
def auth():
    email = request.values.get('email', '', str)
    password = request.values.get('password', '', str)

    result = users.api.auth(session, email, password)
    if result is False:
        return utils.get_error('Неверный Email или пароль')

    user = users.api.get_user_by_email(email)
    admin_log.create_log(request, user)

    return utils.get_answer('Вы успешно авторизовались')


@app.route('/reg', methods=['POST'])
def reg():
    user = utils.get_user(session)
    if user is not None:
        return utils.get_error('Вы уже авторизованы')

    email = request.values.get('email', '', str)
    password = request.values.get('password', '', str)

    password = password.strip()

    if len(password) < 6:
        return utils.get_error('Слишком простой пароль')

    user = users.api.get_user_by_email(email)
    if user is not None:
        return utils.get_error('Данный адрес электронной почты уже занят')

    user = users.api.create_user(email)
    with Session() as db_session:
        user = db_session.query(users.api.User).get(user.id)
        user.password = password
        db_session.commit()
        session['user_id'] = user.id
        session['email'] = user.email
    return utils.get_answer('Вы успешно зарегистрированы')


@app.route('/autochange/set')
def autochange_set():
    user = utils.get_user(session)
    if user is None or user.admin < 2:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    status = request.values.get('status', None)
    start_hour = request.values.get('start_hour', None)
    end_hour = request.values.get('end_hour', None)
    min_minutes = request.values.get('min_minutes', None)
    max_minutes = request.values.get('max_minutes', None)
    min_value = request.values.get('min_value', None)
    max_value = request.values.get('max_value', None)
    ref_id = request.values.get('ref_id', None)

    setting = autochange.AutoChange()

    if status is not None:
        status = int(status)
        if status not in [0, 1]:
            return utils.get_error('Неверное значение статуса')
        setting.status = True if status == 1 else False

    if start_hour is not None:
        start_hour = int(start_hour)
        if start_hour < 0 or start_hour > 23:
            return utils.get_error('Значение должно быть между 0 и 23')
        setting.start_hour = start_hour

    if end_hour is not None:
        end_hour = int(end_hour)
        if end_hour <= setting.start_hour or end_hour > 23:
            return utils.get_error('Значение должно быть между {} и 23'.format(setting.start_hour + 1))
        setting.end_hour = end_hour

    if min_minutes is not None:
        min_minutes = int(min_minutes)
        if min_minutes < 1 or min_minutes > 60:
            return utils.get_error('Значение должно быть между 1 и 60')
        setting.min_minutes = min_minutes

    if max_minutes is not None:
        max_minutes = int(max_minutes)
        if max_minutes <= setting.min_minutes or max_minutes > 60:
            return utils.get_error('Значение должно быть между {} и 23'.format(setting.min_minutes + 1))
        setting.max_minutes = max_minutes

    if min_value is not None:
        min_value = int(min_value)
        if min_value < 1:
            return utils.get_error('Значение должно быть больше 1')
        setting.min_value = min_value

    if max_value is not None:
        max_value = int(max_value)
        if max_value <= setting.min_value:
            return utils.get_error('Значение должно быть больше {}'.format(setting.min_value))
        setting.max_minutes = max_minutes

    if ref_id is not None:
        setting.ref_id = ref_id


    setting.save()
    return utils.get_answer('Сохранено')


@app.route('/settings/set')
def settings_set():
    try:
        user = utils.get_user(session)
        if user is None or user.admin < 2:
            notify.hack_message(request, session)
            return abort(404)

        admin_log.create_log(request, user)

        min_withdraw = request.values.get('min_withdraw', None)
        best_minutes = request.values.get('best_minutes', None)
        proxy = request.values.get('proxy', None)
        order_minutes = request.values.get('order_minutes', None)
        prices_timer = request.values.get('prices_timer', None)
        prices_delay = request.values.get('prices_delay', None)
        tech_stop = request.values.get('tech_stop', None)
        message = request.values.get('message', None)
        cash_text = request.values.get('cash_text', None)
        header_message = request.values.get('header_message', None)
        change_rests = request.values.get('change_rests', None)
        header_text = request.values.get('header_text', None)
        autocommit = request.values.get('autocommit', None)

        setting = settings.Setting()

        if min_withdraw is not None:
            min_withdraw = int(min_withdraw)
            if min_withdraw < 1:
                return utils.get_error('Сумма не может быть меньше единицы')
            setting.min_withdraw = min_withdraw

        if best_minutes is not None:
            best_minutes = int(best_minutes)
            if best_minutes < 1:
                return utils.get_error('Кол-во минут не может быть меньше 1')
            setting.best_minutes = best_minutes

        if proxy is not None:
            setting.proxy = proxy

        if autocommit is not None:
            setting.autocommit = autocommit

        if order_minutes is not None:
            order_minutes = int(order_minutes)
            if order_minutes < 1:
                return utils.get_error('Кол-во минут не может быть меньше 1')
            setting.order_minutes = order_minutes

        if prices_timer is not None:
            prices_timer = int(prices_timer)
            if prices_timer not in [0, 1]:
                return utils.get_error('Неверное значение статуса export.xml')
            setting.prices_timer = True if prices_timer == 1 else False

        if prices_delay is not None:
            prices_delay = int(prices_delay)
            if prices_delay < 10:
                return utils.get_error('Кол-во секунд не может быть меньше 10')
            setting.prices_delay = prices_delay

        if tech_stop is not None:
            tech_stop = int(tech_stop)
            if tech_stop not in [0, 1]:
                return utils.get_error('Неверное значение tech_stop')
            setting.tech_stop = True if tech_stop == 1 else False

        if change_rests is not None:
            change_rests = int(change_rests)
            if change_rests not in [0, 1]:
                return utils.get_error('Неверное значение change_rests')
            setting.change_rests = True if change_rests == 1 else False

        if message is not None:
            setting.message = message

        if cash_text is not None:
            setting.cash_text = cash_text

        if header_text is not None:
            setting.headers = header_text

        if header_message is not None:
            setting.header_message = header_message

        setting.save()
        return utils.get_answer('Сохранено')
    except:
        print(traceback.format_exc())
        notify.send_me(traceback.format_exc())
        return abort(500)


@app.route('/tools/<string:direction>')
def tools_url(direction):
    tools_list = []

    pairs_list = pairs.api.get_pairs()

    if direction == 'from':
        for pair in pairs_list:
            if pair.t_from not in tools_list:
                if pair.t_from.showed is False:
                    continue
                tools_list.append(pair.t_from)

        tools_list.sort(key=lambda tool: tool.sort_from)
        return utils.get_answer('', {'tools': tools_list})
    elif direction == 'to':
        for pair in pairs_list:
            if pair.t_to not in tools_list:
                if pair.t_to.showed is False:
                    continue
                tools_list.append(pair.t_to)

        tools_list.sort(key=lambda tool: tool.sort_to)

        for tool in tools_list:
            tool.reserve = decimal.Decimal(tool.reserve).quantize(decimal.Decimal(tool.rounded_str))
        return utils.get_answer('', {'tools': tools_list})
    return utils.get_error('Invalid direction')


@app.route('/exchange/tool')
def exchange_tool():
    tool_name = request.values.get('tool', '', str)
    network = request.values.get('network', '', str)
    direction = request.values.get('direction', '', str)

    tool = tools.api.get_tool_by_name(tool_name, network)

    pairs_all = pairs.api.get_pairs(False)
    tools_list = []

    for pair in pairs_all:
        if direction == 'from':
            if pair.t_from.id == tool.id:
                if pair.t_to not in tools_list:
                    tools_list.append(pair.t_to)
        elif direction == 'to':
            if pair.t_to.id == tool.id:
                if pair.t_from not in tools_list:
                    tools_list.append(pair.t_from)

    return utils.get_answer('', {'tools': tools_list})


@app.route('/exchange/info')
def exchange_info():
    tool_from = request.values.get('tool_from', 0, int)
    tool_to = request.values.get('tool_to', 0, int)

    pair = pairs.api.get_pair_by_tools(tool_from, tool_to)

    pair.t_from = tools.api.get_tool_by_id(pair.tool_from)
    pair.t_to = tools.api.get_tool_by_id(pair.tool_to)

    pair.get_cost()

    print(pair.t_from, pair.t_to)
    print(pair.cost)

    try:
        pair.get_min_max()
    except:

        pair.status = False


    return utils.get_answer('', {'pair': pair})


@app.route('/exchange/create')
def exchange_create():
    print('1')
    create_token = request.values.get('create_token', '', str)
    tool_from = request.values.get('tool_from', '', str)
    tool_to = request.values.get('tool_to', '', str)
    email = request.values.get('email', '', str)
    give_amount = request.values.get('give_amount', 0.0, float)

    from_wallet = request.values.get('from_wallet', '', str)
    to_wallet = request.values.get('to_wallet', '', str)

    cash_station = request.values.get('cash_station', '', str)
    cash_name = request.values.get('cash_name', '', str)
    cash_telegram = request.values.get('cash_telegram', '', str)
    cash_wallet = request.values.get('cash_wallet', '', str)

    ref_id = request.values.get('ref_id', '', str)

    pair = pairs.api.get_pair_by_tools(tool_from, tool_to)
    print('12')

    if len(create_token) == 0:
        return utils.get_error('Обновите страницу')

    if create_token not in create_tokens:
        return utils.get_error('Обновите страницу')


    if pair is None:
        return utils.get_error('Пара не найдена')

    try:
        order = orders.api.create_order(email, pair, give_amount, to_wallet, from_wallet, cash_station=cash_station,
                                        cash_name=cash_name, cash_telegram=cash_telegram, ref_id=ref_id, cash_wallet=cash_wallet)
    except IncorrectDataValue as e:
        return utils.get_error(e.message)
    except Exception as e:
        print(traceback.format_exc())
        return utils.get_error(e.args[0])

    if order is False:
        return utils.get_answer('', {'need_verification': True, 'order': None})

    session['client_email'] = email
    create_tokens.remove(create_token)

    return utils.get_answer('', {'need_verification': False, 'order': order})


@app.route('/order/<string:code>')
def order_get(code):
    user = utils.get_user(session)

    order = orders.api.get_order_by_code(code)
    if order.client_id != user.id:
        return abort(403)

    return utils.get_answer('', {'info': order.get_html_info()})


@app.route('/change_pass')
def change_pass():
    user = utils.get_user(session)
    if user is None:
        return abort(403)

    old_pas = request.values.get('old_pas', '', str)
    new_pas = request.values.get('new_pas', '', str)

    if user.password != old_pas:
        return utils.get_error('Неверный пароль')

    new_pas = new_pas.strip()

    if len(new_pas) < 6:
        return utils.get_error('Слишком простой пароль')

    with Session() as db_session:
        usr = db_session.query(users.api.User).get(user.id)
        usr.password = new_pas
        db_session.commit()

    return utils.get_answer('Пароль успешно изменён')


@app.route('/ref_transaction/remove')
def ref_transaction_remove():
    user = utils.get_user(session)
    if user is None or user.admin < 2:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    transaction_id = request.values.get('id', 0, int)

    try:
        orders.api.remove_ref_transaction(transaction_id)
    except IncorrectDataValue as e:
        return utils.get_error(e.message)
    except Exception as e:
        return utils.get_error(e.args[0])

    return utils.get_answer('Транзакция успешно удалена')


@app.route('/autochange/upload')
def autochange_upload():
    user = utils.get_user(session)
    if user is None or user.admin < 2:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    file_uuid = request.values.get('file_uuid', '', str)

    try:
        autochange.api.upload_file(file_uuid)
    except IncorrectDataValue as e:
        print('aga')
        return utils.get_error(e.message)
    except Exception as e:
        print(e.args)
        return utils.get_error(e.args[0])

    setting = autochange.AutoChange()
    setting.user_id = 0
    setting.save()

    emails = autochange.api.get_users_list()
    return utils.get_answer('Успешно загружено.<br><br>Кол-во Email в БД: {}<br>Текущий индекс: 0'.format(len(emails)))