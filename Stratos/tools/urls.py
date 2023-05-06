from flask import blueprints, session, request, abort, redirect, render_template
from errors import *
from db import Session
import utils
import tools
import whitebit
import files
import shutil
import admin_log
import notify

app = blueprints.Blueprint('Tools', __name__, url_prefix='/api/tools')


@app.route('/')
def home():
    return 'Tools API'


@app.route('/networks')
def networks():
    user = utils.get_user(session)
    if user is None or user.admin < 1:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    tool_name = request.values.get('name', '', str)
    return utils.get_answer('', {'networks': whitebit.api.get_networks(tool_name)})


@app.route('/get')
def get():
    user = utils.get_user(session)
    if user is None or user.admin < 1:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    tool_id = request.values.get('id', 0, int)
    if tool_id != 0:
        return utils.get_answer('', {'tool': tools.api.get_tool_by_id(tool_id)})
    else:
        tools_list = tools.api.get_tools()
        for tool in tools_list:
            print(tool)
        return utils.get_answer('', {'tools': tools.api.get_tools()})


@app.route('/create')
def create():
    user = utils.get_user(session)
    if user is None or user.admin < 2:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    name = request.values.get('name', '', str)
    nickname = request.values.get('nickname', '', str)
    xml_code = request.values.get('xml_code', '', str)
    wallet = request.values.get('wallet', '', str)
    min_payment = request.values.get('min_payment', 0.0, float)
    max_payment = request.values.get('max_payment', 0.0, float)
    sort_from = request.values.get('sort_from', 0, int)
    sort_to = request.values.get('sort_to', 0, int)
    placeholder_from = request.values.get('placeholder_from', '', str)
    placeholder_to = request.values.get('placeholder_to', '', str)
    reserve = request.values.get('reserve', 0.0, float)
    rounded = request.values.get('rounded', '', str)
    cost_link = request.values.get('cost_link', '', str)
    is_cash = request.values.get('is_cash', 0, int)
    accept_count = request.values.get('accept_count', 0, int)
    network = request.values.get('network', '', str)

    if is_cash == 0:
        is_cash = False
    else:
        is_cash = True

    try:
        tool = tools.api.create_tool(name, nickname, wallet, min_payment, max_payment, reserve, sort_from, sort_to,
                                     accept_count, placeholder_from, placeholder_to, is_cash, rounded, xml_code, network, cost_link)
    except IncorrectDataValue as e:
        return utils.get_error(e.message)
    except Exception as e:
        return utils.get_error(e.args[0])
    return utils.get_answer('', {'tool': tool})


@app.route('/edit')
def edit():
    user = utils.get_user(session)
    if user is None or user.admin < 2:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    tool_id = request.values.get('id', 0, int)
    nickname = request.values.get('nickname', None)
    xml_code = request.values.get('xml_code', None)
    wallet = request.values.get('wallet', None)
    min_payment = request.values.get('min_payment', None)
    max_payment = request.values.get('max_payment', None)
    sort_from = request.values.get('sort_from', None)
    sort_to = request.values.get('sort_to', None)
    placeholder_from = request.values.get('placeholder_from', None)
    placeholder_to = request.values.get('placeholder_to', None)
    reserve = request.values.get('reserve', None)
    rounded = request.values.get('rounded', None)
    cost_link = request.values.get('cost_link', None)
    showed = request.values.get('showed', None)
    accept_count = request.values.get('accept_count', None)
    best_code = request.values.get('best_code', None)
    best_city = request.values.get('best_city', None)
    show_fio = request.values.get('show_fio', None)

    with Session() as db_session:
        tool = db_session.query(tools.api.Tool).get(tool_id)

        if nickname is not None:
            if len(nickname) == 0:
                db_session.close()
                return utils.get_error('Никнейм не может быть пустым')
            tool.nickname = nickname

        if show_fio is not None:
            show_fio = int(show_fio)
            show_fio = True if show_fio == 1 else False
            tool.show_fio = show_fio

        if best_city is not None:
            tool.best_city = best_city
        if best_code is not None:
            tool.best_code = best_code
        if xml_code is not None:
            if len(xml_code) == 0:
                db_session.close()
                return utils.get_error('xml_code не может быть пустым')
            tool.xml_code = xml_code
        if wallet is not None:
            if len(wallet) == 0:
                db_session.close()
                return utils.get_error('wallet не может быть пустым')
            tool.wallet = wallet
        if min_payment is not None:
            if float(min_payment) < 0:
                db_session.close()
                return utils.get_error('min_payment не может быть < 0')
            tool.min_payment = min_payment
        if max_payment is not None:
            if float(max_payment) <= float(tool.min_payment):
                db_session.close()
                return utils.get_error('max_payment не может быть <= min_payment')
            tool.max_payment = max_payment
        if sort_from is not None:
            tool.sort_from = sort_from
        if sort_to is not None:
            tool.sort_to = sort_to
        if placeholder_from is not None:
            tool.placeholder_from = placeholder_from
        if placeholder_to is not None:
            tool.placeholder_to = placeholder_to
        print(reserve)
        if reserve is not None:
            tool.reserve = reserve
        if rounded is not None:
            if str(rounded) == '0':
                tool.rounded_str = rounded
            else:
                if str(rounded).startswith('0.0') is False:
                    db_session.close()
                    return utils.get_error('Строка округления должна начинаться на 0.0')

                check_round_str = True
                for symbol in rounded:
                    if symbol not in ['0', '.']:
                        check_round_str = False

                if check_round_str is False:
                    db_session.close()
                    return utils.get_error('Строка округления должна начинаться на 0.0')
                tool.rounded_str = rounded
        if cost_link is not None:
            tool.cost_link = cost_link
        if showed is not None:
            if int(showed) == 1:
                tool.showed = True
            else:
                tool.showed = False
        if accept_count is not None:
            tool.accept_count = accept_count

        db_session.commit()
    return utils.get_answer('')


@app.route('/edit/icon')
def edit_icon():
    user = utils.get_user(session)
    if user is None or user.admin < 2:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    tool_id = request.values.get('id', 0, int)
    uuid = request.values.get('uuid', '', str)

    file = files.api.get_file(uuid)
    tool = tools.api.get_tool_by_id(tool_id)
    shutil.copyfile('{}/storage/{}.{}'.format(utils.get_script_dir(), file.uuid, file.extension),
                    '{}/static/icons/{}.png'.format(utils.get_script_dir(), tool.name))
    return utils.get_answer('Сохранено')


@app.before_request
def before():
    user = utils.get_user(session)
    if user is None:
        notify.hack_message(request, session)
        return abort(403)
    if user.admin == 0:
        notify.hack_message(request, session)
        return abort(403)