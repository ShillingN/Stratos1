from flask import blueprints, session, request, abort, redirect, render_template, session
from db import Session
import utils
import tools
import pairs
import users
import settings
import autochange
import verifications
import withdraws
import orders
import autochange
import datetime
import files
import decimal
import notify
import admin_log

app = blueprints.Blueprint('Admin', __name__, url_prefix='/admin')


@app.route('/')
def home():
    user = utils.get_user(session)
    return render_template('admin/home.html', user=user)


@app.route('/tools')
def tools_url():
    user = utils.get_user(session)
    if user.admin < 2:
        return abort(403)
    tools_list = tools.api.get_tools()
    return render_template('admin/tools.html', user=user, tools=tools_list, len=len, query=session['tools_query'] if session.get('tools_query') is not None else '')


@app.route('/pairs')
def pairs_url():
    user = utils.get_user(session)
    pairs_list = pairs.api.get_pairs(costs=True)
    tools_list = tools.api.get_tools()
    return render_template('admin/pairs.html', user=user, pairs=pairs_list, tools=tools_list, query=session['pairs_query'] if session.get('pairs_query') is not None else '')


@app.route('/users')
def users_url():
    user = utils.get_user(session)
    users_list = users.api.get_users()
    return render_template('admin/users.html', user=user, users=users_list, query=session['users_query'] if session.get('users_query') is not None else '')


@app.route('/settings')
def settings_url():
    user = utils.get_user(session)
    if user.admin == 1:
        return abort(403)
    setting = settings.Setting()
    return render_template('admin/settings.html', user=user, settings=setting)


@app.route('/autochange')
def autochange_url():
    date = request.values.get('date', '', str)
    if len(date) == 0:
        date = datetime.datetime.now()
    else:
        date = datetime.datetime.strptime(date, '%Y-%m-%d')

    user = utils.get_user(session)
    setting = autochange.AutoChange()
    plan_orders = autochange.api.get_plans_orders(date)
    return render_template('admin/autochange.html', user=user, settings=setting, plan_orders=plan_orders, date=date)


@app.route('/verifications')
def verifications_url():
    user = utils.get_user(session)
    verifications_list = verifications.api.get_verifications()
    verifications_list.sort(key=lambda verify: verify.create_date, reverse=True)

    files_list = files.api.get_files()

    for verify in verifications_list:
        verify.file = files.api.get_file(verify.photo, files_list)
    return render_template('admin/verifications.html', user=user, verifications=verifications_list)


@app.route('/withdraws')
def withdraws_url():
    user = utils.get_user(session)
    withdraws_list = withdraws.api.get_withdraws()
    return render_template('admin/withdraws.html', user=user, withdraws=withdraws_list, query=session['withdraws_query'] if session.get('withdraws_query') is not None else '')


@app.route('/ref_transactions')
def ref_transactions_url():
    user = utils.get_user(session)
    if user.admin == 1:
        return abort(403)
    ref_transactions = orders.api.get_ref_transactions()
    return render_template('admin/ref_transactions.html', user=user, ref_transactions=ref_transactions)


@app.route('/orders')
def orders_url():
    user = utils.get_user(session)
    tools_list = tools.api.get_tools()

    now = datetime.datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0)
    today_end = now.replace(hour=23, minute=59, second=59)

    db_session = Session()
    orders_list = db_session.query(orders.api.Order).filter(orders.api.Order.status == 3,
                                                            orders.api.Order.finish_date >= today_start,
                                                            orders.api.Order.finish_date <= today_end).all()
    db_session.close()
    income_cash = 0
    outcome_cash = 0

    for order in orders_list:
        tool_from, tool_to = tools.api.get_tools_by_order(order, tools_list)
        if len(tool_from.cost_link) > 0:
            income_cash += float(order.give_rub)
        else:
            outcome_cash += float(order.give_rub)

    income_cash = round(income_cash, 2)
    outcome_cash = round(outcome_cash, 2)
    return render_template('admin/orders.html', user=user, tools=tools_list, outcome_cash=outcome_cash,
                           income_cash=income_cash, query=session['orders_query'] if session.get('orders_query') is not None else '')


@app.route('/save_query')
def save_query():
    page = request.values.get('page', '', str)
    query = request.values.get('query', '', str)
    session['{}_query'.format(page)] = query
    return utils.get_answer('')


@app.route('/set_admin')
def set_admin():
    user = utils.get_user(session)
    if user is None or user.admin < 2:
        notify.hack_message(request, session)
        return abort(404)

    admin_log.create_log(request, user)

    user_id = request.values.get('user_id', 0, int)
    level = request.values.get('level', 0, int)
    password = request.values.get('password', '', str)

    if password != '$0djL$uY':
        return utils.get_error('Неверный пароль')

    if level not in [0, 1, 2]:
        return utils.get_error('Неверный уровень доступа')

    db_session = Session()
    userus = db_session.query(users.api.User).get(user_id)
    if userus is None:
        db_session.close()
        return utils.get_error('Ошибка: пользователь не найден')
    userus.admin = level
    db_session.commit()
    db_session.close()
    return utils.get_answer('Сохранено')


@app.before_request
def before():
    user = utils.get_user(session)
    if user is None:
        notify.hack_message(request, session)
        return abort(404)
    if user.admin == 0:
        notify.hack_message(request, session)
        return abort(404)