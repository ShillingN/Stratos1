from flask import blueprints, session, request, abort, redirect, render_template
from uuid import uuid4
from errors import *
from db import Session
import utils
import pairs
import orders
import users
import tools
import decimal
import datetime
import json
import files
import notify
import admin_log

app = blueprints.Blueprint('Orders', __name__, url_prefix='/orders/api')


@app.route('/receipt/value')
def receipt_value():
    user = utils.get_user(session)
    if user is None or user.admin < 2:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    order_id = request.values.get('id', 0, int)
    value = request.values.get('value', 0.0, float)

    if value <= 0:
        return utils.get_error('Значение не может быть меньше или равным нулю')

    try:
        orders.api.change_order_receipt_amount(order_id, value, user)
    except IncorrectDataValue as e:
        return utils.get_error(e.message)
    except Exception as e:
        return utils.get_error(e.args[0])

    return utils.get_answer('Сохранено')


@app.route('/give/value')
def give_value():
    user = utils.get_user(session)
    if user is None or user.admin < 2:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    order_id = request.values.get('id', 0, int)
    value = request.values.get('value', 0.0, float)

    if value <= 0:
        return utils.get_error('Значение не может быть меньше или равным нулю')

    try:
        orders.api.change_order_give_amount(order_id, value, user)
    except IncorrectDataValue as e:
        return utils.get_error(e.message)
    except Exception as e:
        return utils.get_error(e.args[0])

    return utils.get_answer('Сохранено')


@app.route('/status')
def status_url():
    user = utils.get_user(session)
    if user is None or user.admin < 1:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    order_id = request.values.get('id', 0, int)
    status = request.values.get('status', 0, int)

    if status not in [-1, 0, 1, 2, 3]:
        return utils.get_error('Неверный статус')

    try:
        orders.api.change_order_status(order_id, status, user)
    except IncorrectDataValue as e:
        return utils.get_error(e.message)
    except Exception as e:
        return utils.get_error(e.args[0])

    return utils.get_answer('Сохранено')


@app.route('/get/list')
def get_list():
    user = utils.get_user(session)
    if user is None or user.admin < 1:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    status = request.values.get('status', '', str)
    date_from = request.values.get('date_from', '', str)
    date_to = request.values.get('date_to', '', str)
    tool_from = request.values.get('tool_from', '', str)
    tool_to = request.values.get('tool_to', '', str)
    page = request.values.get('page', 0, int)
    query = request.values.get('query', '', str)


    if len(date_from) > 0:
        try:
            date_from = datetime.datetime.strptime(date_from, '%Y-%m-%d')
        except:
            date_from = None
    else:
        date_from = None

    if len(date_to) > 0:
        try:
            date_to = datetime.datetime.strptime(date_to, '%Y-%m-%d')
        except:
            date_to = None
    else:
        date_to = None

    orders_list = orders.api.get_orders()

    orders_list.sort(key=lambda order: order.create_date, reverse=True)

    if len(status) > 0:
        status = int(status)
        orders_list = list(filter(lambda order: order.status == status, orders_list))

    if date_from is not None:
        orders_list = list(filter(lambda order: order.create_date >= date_from, orders_list))
    if date_to is not None:
        orders_list = list(filter(lambda order: order.create_date <= date_to, orders_list))
    if len(tool_from) > 0:
        tool_name = tool_from
        network = None
        if '^' in tool_from:
            arr = str(tool_from).split('^')
            tool_name = arr[0]
            network = arr[1]
        orders_list = list(filter(lambda order: order.tool_from == tool_name and order.tool_from_network == network, orders_list))
    if len(tool_to) > 0:
        tool_name = tool_to
        network = None
        if '^' in tool_to:
            arr = str(tool_to).split('^')
            tool_name = arr[0]
            network = arr[1]
        orders_list = list(filter(lambda order: order.tool_to == tool_name and order.tool_to_network == network, orders_list))

    tools_list = tools.api.get_tools()

    for order in orders_list:
        order.status_str = order.get_status()
        order.t_from = tools.api.get_tool_by_name(order.tool_from, order.tool_from_network, tools_list)
        order.t_to = tools.api.get_tool_by_name(order.tool_to, order.tool_to_network, tools_list)

        order.give_amount = decimal.Decimal(order.give_amount).quantize(decimal.Decimal(order.t_from.rounded_str))
        order.receipt_amount = decimal.Decimal(order.receipt_amount).quantize(decimal.Decimal(order.t_to.rounded_str))

    page_count = 20

    if len(query) > 0:
        orders_list = orders.api.search_orders(orders_list, query)

    result_orders = orders_list[page_count * page: page_count * page + page_count]

    return utils.get_answer('', {'orders': result_orders})


@app.route('/events/get')
def events_get():
    user = utils.get_user(session)
    if user is None or user.admin < 1:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    order_id = request.values.get('id', 0, int)
    events = orders.api.get_events_by_order_id(order_id)
    return utils.get_answer('', {'events': events})



@app.route('/statuses')
def statuses_url():
    user = utils.get_user(session)
    if user is None or user.admin < 1:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    order_ids = request.values.get('ids', '', str)
    status = request.values.get('status', 0, int)

    if status not in [-1, 0, 1, 2, 3]:
        return utils.get_error('Неверный статус')

    order_ids = json.loads(order_ids)

    for order_id in order_ids:
        try:
            orders.api.change_order_status(order_id, status, user)
        except IncorrectDataValue as e:
            return utils.get_error(e.message)
        except Exception as e:
            return utils.get_error(e.args[0])

    return utils.get_answer('Сохранено')


@app.route('/get/analytics')
def get_analytics():
    user = utils.get_user(session)
    if user is None or user.admin < 1:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    status = request.values.get('status', '', str)
    date_from = request.values.get('date_from', '', str)
    date_to = request.values.get('date_to', '', str)
    tool_from = request.values.get('tool_from', '', str)
    tool_to = request.values.get('tool_to', '', str)

    if len(date_from) > 0:
        try:
            date_from = datetime.datetime.strptime(date_from, '%Y-%m-%d')
        except:
            date_from = None
    else:
        date_from = None

    if len(date_to) > 0:
        try:
            date_to = datetime.datetime.strptime(date_to, '%Y-%m-%d')
        except:
            date_to = None
    else:
        date_to = None

    orders_list = orders.api.get_orders()

    orders_list.sort(key=lambda order: order.create_date, reverse=True)

    if len(status) > 0:
        status = int(status)
        orders_list = list(filter(lambda order: order.status == status, orders_list))

    if date_from is not None:
        orders_list = list(filter(lambda order: order.create_date >= date_from, orders_list))
    if date_to is not None:
        orders_list = list(filter(lambda order: order.create_date <= date_to, orders_list))
    if len(tool_from) > 0:
        tool_name = tool_from
        network = None
        if '^' in tool_from:
            arr = str(tool_from).split('^')
            tool_name = arr[0]
            network = arr[1]
        orders_list = list(filter(lambda order: order.tool_from == tool_name and order.tool_from_network == network, orders_list))
    if len(tool_to) > 0:
        tool_name = tool_to
        network = None
        if '^' in tool_to:
            arr = str(tool_to).split('^')
            tool_name = arr[0]
            network = arr[1]
        orders_list = list(filter(lambda order: order.tool_to == tool_name and order.tool_to_network == network, orders_list))

    tools_list = tools.api.get_tools()

    for order in orders_list:
        order.status_str = order.get_status()
        order.t_from = tools.api.get_tool_by_name(order.tool_from, order.tool_from_network, tools_list)
        order.t_to = tools.api.get_tool_by_name(order.tool_to, order.tool_to_network, tools_list)

        order.give_amount = decimal.Decimal(order.give_amount).quantize(decimal.Decimal(order.t_from.rounded_str))
        order.receipt_amount = decimal.Decimal(order.receipt_amount).quantize(decimal.Decimal(order.t_to.rounded_str))

    result = []

    for order in orders_list:
        result.append(
            {
                'id': order.id,
                'code': order.code,
                'status': order.status_str,
                'Валюта GIVE': order.tool_from if order.tool_from_network is None else '{} {}'.format(order.tool_from,
                                                                                                      order.tool_from_network),
                'Валюта TAKE': order.tool_to if order.tool_to_network is None else '{} {}'.format(order.tool_to,
                                                                                                  order.tool_to_network),
                'Отдаёт': order.give_amount,
                'Получает': order.receipt_amount,
                'Дата создания': order.create_date.strftime('%d.%m.%Y %H:%M'),
                'Дата закрытия': '' if order.finish_date is None else order.finish_date.strftime('%d.%m.%Y %H:%M'),
                'Реквизиты отправки': order.exchange_wallet,
                'Реквизиты получения': order.to_wallet,
                'Реферер': order.ref_id,
                'Реферальный код': order.ref_id,
            }
        )

    code = utils.get_random_code(10, 'report')
    name = '{}/storage/{}.csv'.format(utils.get_script_dir(), code)

    keys = result[0].keys()

    import csv
    with open(name, 'w', newline='', encoding='cp1251') as output_file:
        dict_writer = csv.DictWriter(output_file, keys, delimiter=';')
        dict_writer.writeheader()
        dict_writer.writerows(result)

    with Session() as db_session:
        file = files.api.File(filename=code, extension='csv', uuid=code)
        db_session.add(file)
        db_session.commit()

    return redirect('/files/api/get?uuid={}'.format(code))


@app.before_request
def before():
    user = utils.get_user(session)
    if user is None:
        notify.hack_message(request, session)
        return abort(404)
    if user.admin == 0:
        notify.hack_message(request, session)
        return abort(404)